"""Reproducible retail analytics. Run: python src/pipeline.py [--download]."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import sys
import urllib.request
import zipfile
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://archive.ics.uci.edu/dataset/502/online+retail+ii"
DOWNLOAD = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
RAW = ROOT / "data/raw/online_retail_II.xlsx"
OUT = ROOT / "data/processed"


def clean(raw: pd.DataFrame):
    """Assign one mutually exclusive disposition to every original source row."""
    d = raw.copy()
    for col in ["invoice", "stock_code", "description", "country"]:
        d[col] = d[col].fillna("").astype(str).str.strip()
    d["country"] = d.country.replace("", "Unknown")
    d["invoice_date"] = pd.to_datetime(d.invoice_date, errors="coerce")
    d["quantity"] = pd.to_numeric(d.quantity, errors="coerce")
    d["unit_price"] = pd.to_numeric(d.unit_price, errors="coerce")
    cid = pd.to_numeric(d.customer_id, errors="coerce")
    d["customer_id"] = cid.where(cid.notna() & (cid % 1 == 0)).astype("Int64").astype("string")
    keys = ["invoice", "stock_code", "description", "quantity", "invoice_date", "unit_price", "customer_id", "country"]
    duplicates = d.duplicated(keys, keep="first")
    invalid = (d.invoice.eq("") | d.stock_code.eq("") | d.invoice_date.isna()
               | ~np.isfinite(d.quantity) | ~np.isfinite(d.unit_price)
               | d.quantity.mod(1).ne(0) | (d.unit_price * 100).abs().gt(1e12))
    # Restrict merchandise to the usual five-digit stock-code family; report excluded codes.
    merchandise = d.stock_code.str.fullmatch(r"\d{5}[A-Za-z]{0,2}", na=False)
    cancelled = d.invoice.str.upper().str.startswith("C")
    d["disposition"] = np.select(
        [duplicates, invalid, ~merchandise, d.unit_price.le(0), d.quantity.eq(0), cancelled & d.quantity.gt(0)],
        ["duplicate", "invalid_required_value", "non_merchandise_code", "nonpositive_price", "zero_quantity", "positive_cancellation"],
        default="retained")
    ledger = d.loc[d.disposition.eq("retained")].copy()
    ledger["quantity"] = ledger.quantity.astype("int64")
    # Preserve sub-penny unit prices; round each complete line once using decimal arithmetic.
    price_map = {p:Decimal(str(p)) for p in ledger.unit_price.unique()}
    ledger["unit_price_gbp"] = ledger.unit_price
    ledger["amount_pence"] = np.fromiter(
        (int((price_map[p]*int(q)*100).quantize(Decimal('1'),rounding=ROUND_HALF_EVEN))
         for p,q in zip(ledger.unit_price,ledger.quantity)),dtype=np.int64,count=len(ledger))
    ledger["kind"] = np.where(ledger.quantity.gt(0), "sale", "return")
    ledger["month"] = ledger.invoice_date.dt.strftime("%Y-%m")
    ledger["order_date"] = ledger.invoice_date.dt.strftime("%Y-%m-%d")
    ledger["invoice_date"] = ledger.invoice_date.dt.strftime("%Y-%m-%d %H:%M:%S")
    columns = ["source_sheet", "source_row", "invoice", "stock_code", "description", "quantity", "invoice_date", "order_date", "month", "unit_price_gbp", "amount_pence", "customer_id", "country", "kind"]
    quality = d.groupby("disposition", dropna=False).size().rename("rows").reset_index()
    exclusions = d.loc[d.disposition.eq("non_merchandise_code")].groupby("stock_code").size().rename("rows").reset_index().sort_values("rows", ascending=False)
    return ledger[columns], quality, exclusions


def wilson(success: int, n: int):
    if not n:
        return None, None
    z = 1.959963984540054
    p = success / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n)) / den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / den
    return center-half, center+half


def repeat_study(orders: pd.DataFrame, end: pd.Timestamp):
    """Customer-level, equal 90-day follow-up; no returns in purchase outcome."""
    o = orders.copy()
    o["invoice_date"] = pd.to_datetime(o.invoice_date)
    o = o.sort_values(["customer_id", "invoice_date", "invoice"])
    first = o.drop_duplicates("customer_id").set_index("customer_id")[["invoice", "invoice_date", "sales_pence"]]
    first.columns = ["first_invoice", "first_date", "first_sales_pence"]
    follow = o.join(first, on="customer_id")
    follow["repeat90"] = (follow.invoice.ne(follow.first_invoice)
                           & follow.invoice_date.gt(follow.first_date)
                           & follow.invoice_date.le(follow.first_date + pd.Timedelta(days=90)))
    first["repeat90"] = follow.groupby("customer_id").repeat90.any()
    eligible = first.loc[first.first_date.le(end-pd.Timedelta(days=90))].copy()
    median = float(eligible.first_sales_pence.median())
    eligible["group"] = np.where(eligible.first_sales_pence.gt(median), "Above median", "At or below median")
    groups = []
    for name, g in eligible.groupby("group", sort=True):
        s, n = int(g.repeat90.sum()), len(g)
        low, high = wilson(s, n)
        groups.append(dict(group=name, customers=n, repeat_customers=s, repeat_rate=s/n, ci_low=low, ci_high=high))
    high, low = groups[0], groups[1]
    pooled = (high["repeat_customers"]+low["repeat_customers"]) / len(eligible)
    se0 = math.sqrt(pooled*(1-pooled)*(1/high["customers"]+1/low["customers"]))
    diff = high["repeat_rate"] - low["repeat_rate"]
    z = diff/se0 if se0 else 0
    se = math.sqrt(sum(g["repeat_rate"]*(1-g["repeat_rate"])/g["customers"] for g in groups))
    study = dict(question="Is first observed order size associated with another purchase within 90 days?",
                 hypothesis="H0: the two groups have equal 90-day repeat-purchase rates (two-sided).",
                 followup_days=90, eligible_customers=len(eligible), excluded_recent_customers=len(first)-len(eligible),
                 first_order_median_gbp=median/100, groups=groups, difference=diff,
                 difference_ci_low=diff-1.959963984540054*se, difference_ci_high=diff+1.959963984540054*se,
                 z_statistic=z, p_value=math.erfc(abs(z)/math.sqrt(2)), alpha=0.05,
                 method="Two-sided pooled two-proportion z-test; Wilson group CIs; unpooled Wald difference CI.",
                 limitations="Observational association; no causal effect. First observed order may not be acquisition. Country, season and wholesale mix may confound results. Same-timestamp invoices do not count as a subsequent purchase.")
    return eligible.reset_index(), study


def rfm_customers(orders: pd.DataFrame, end: pd.Timestamp):
    o = orders.copy()
    o["invoice_date"] = pd.to_datetime(o.invoice_date)
    r = o.groupby("customer_id").agg(last_purchase=("invoice_date", "max"), first_purchase=("invoice_date", "min"), frequency=("invoice", "nunique"), monetary_pence=("sales_pence", "sum")).reset_index()
    snapshot = end.normalize() + pd.Timedelta(days=1)
    r["recency_days"] = (snapshot-r.last_purchase.dt.normalize()).dt.days
    for name, ascending in [("recency_days",False),("frequency",True),("monetary_pence",True)]:
        r[{"recency_days":"r_score","frequency":"f_score","monetary_pence":"m_score"}[name]] = np.ceil(r[name].rank(method="average",pct=True,ascending=ascending)*5).clip(1,5).astype(int)
    r["rfm_score"] = r.r_score.astype(str)+r.f_score.astype(str)+r.m_score.astype(str)
    r["segment"] = np.select([
        r.r_score.ge(4)&r.f_score.ge(4), r.r_score.ge(4)&r.f_score.ge(2), r.r_score.ge(4),
        r.r_score.le(2)&r.f_score.ge(3), r.r_score.le(2)&r.f_score.le(2)],
        ["Champions","Recent repeat buyers","Recent low-frequency buyers","At risk","Hibernating"],default="Needs attention")
    r["monetary_gbp"] = r.monetary_pence/100
    return r, snapshot


def cohort_table(orders: pd.DataFrame, end: pd.Timestamp):
    o = orders.copy()
    o["activity_month"] = pd.to_datetime(o.invoice_date).dt.to_period("M")
    o["cohort"] = o.groupby("customer_id").activity_month.transform("min")
    o["age"] = (o.activity_month.dt.year-o.cohort.dt.year)*12+o.activity_month.dt.month-o.cohort.dt.month
    counts = o.groupby(["cohort","age"]).customer_id.nunique()
    last_complete = end.to_period("M")-1 if end.normalize() < (end.to_period("M").end_time.normalize()) else end.to_period("M")
    rows = []
    for cohort in sorted(o.cohort.unique()):
        if cohort > last_complete:
            continue
        base = int(counts.get((cohort,0),0))
        for age in range(13):
            observed = cohort+age <= last_complete
            active = int(counts.get((cohort,age),0)) if observed else None
            rows.append(dict(cohort=str(cohort),age=age,cohort_customers=base,active_customers=active,
                             retention=active/base if observed else None,observed=int(observed)))
    return pd.DataFrame(rows)


def records(d):
    return json.loads(d.to_json(orient="records",date_format="iso"))


def run(download=False):
    OUT.mkdir(parents=True,exist_ok=True)
    (ROOT/"reports").mkdir(exist_ok=True)
    if not RAW.exists():
        if not download:
            raise FileNotFoundError("Place online_retail_II.xlsx in data/raw or run with --download")
        RAW.parent.mkdir(parents=True,exist_ok=True)
        target = RAW.parent/"source.zip"
        urllib.request.urlretrieve(DOWNLOAD,target)
        with zipfile.ZipFile(target) as z:
            member = next(x for x in z.namelist() if x.endswith(".xlsx"))
            RAW.write_bytes(z.read(member))
        target.unlink()
    checksum = hashlib.sha256(RAW.read_bytes()).hexdigest()
    print("Reading both source worksheets...",flush=True)
    sheets = pd.read_excel(RAW,sheet_name=None,engine="openpyxl")
    frames=[]
    mapping={"Invoice":"invoice","StockCode":"stock_code","Description":"description","Quantity":"quantity","InvoiceDate":"invoice_date","Price":"unit_price","Customer ID":"customer_id","Country":"country"}
    for name, d in sheets.items():
        d=d.rename(columns=mapping)
        d["source_sheet"],d["source_row"]=name,np.arange(2,len(d)+2)
        frames.append(d)
    raw=pd.concat(frames,ignore_index=True)
    ledger,quality,exclusions=clean(raw)
    print(f"Read {len(raw):,} rows; retained {len(ledger):,}. Building SQL database...",flush=True)
    db=OUT/"retail.sqlite"
    con=sqlite3.connect(db)
    ledger.to_sql("ledger",con,if_exists="replace",index=False,chunksize=20000)
    con.executescript((ROOT/"sql/01_build.sql").read_text(encoding="utf-8"))
    tables={}
    for name in ["monthly_sales","country_sales","product_sales","orders","customer_orders","country_monthly"]:
        tables[name]=pd.read_sql_query(f"SELECT * FROM {name}",con)
    orders=tables["customer_orders"]
    end=pd.to_datetime(ledger.invoice_date).max()
    rfm,snapshot=rfm_customers(orders,end)
    cohorts=cohort_table(orders,end)
    study_customers,study=repeat_study(orders,end)
    segments=rfm.groupby("segment").agg(customers=("customer_id","size"),sales_pence=("monetary_pence","sum"),orders=("frequency","sum")).reset_index().sort_values("sales_pence",ascending=False)
    segments["customer_share"]=segments.customers/len(rfm)
    segments["sales_share"]=segments.sales_pence/segments.sales_pence.sum()
    for name,table in [("rfm_customers",rfm),("cohort_retention",cohorts),("repeat_study_customers",study_customers),("customer_segments",segments)]:
        table.to_sql(name,con,if_exists="replace",index=False)
        tables[name]=table
    quality.to_csv(OUT/"data_quality.csv",index=False)
    exclusions.to_csv(OUT/"excluded_stock_codes.csv",index=False)
    ledger.to_csv(OUT/"ledger.csv.gz",index=False,compression="gzip")
    for name,d in tables.items():
        # Order-level files make Power BI relationships straightforward.
        d.to_csv(OUT/f"{name}.csv",index=False)
    identified=ledger.customer_id.notna()
    sales=ledger.kind.eq("sale")
    gross=int(ledger.loc[sales,"amount_pence"].sum())
    returns=-int(ledger.loc[~sales,"amount_pence"].sum())
    repeat_n=int(rfm.frequency.ge(2).sum())
    summary=dict(raw_rows=len(raw),retained_rows=len(ledger),excluded_rows=len(raw)-len(ledger),
        source_rows_by_sheet={n:len(d) for n,d in sheets.items()},source_sha256=checksum,source_url=SOURCE,
        period_start=ledger.invoice_date.min(),period_end=ledger.invoice_date.max(),snapshot_date=str(snapshot.date()),
        gross_sales_gbp=gross/100,returns_gbp=returns/100,net_sales_gbp=(gross-returns)/100,
        orders=len(tables["orders"]),identified_customers=len(rfm),repeat_customers=repeat_n,repeat_customer_rate=repeat_n/len(rfm),
        average_order_value_gbp=gross/100/len(tables["orders"]),
        identified_sales_gbp=int(ledger.loc[identified&sales,"amount_pence"].sum())/100,
        unidentified_sales_gbp=int(ledger.loc[~identified&sales,"amount_pence"].sum())/100,
        quality=records(quality),study=study)
    # Independent group reconciliations catch dropped rows, duplicated joins and sign errors.
    assert int(tables["monthly_sales"].net_sales_pence.sum()) == gross-returns
    assert int(tables["country_sales"].gross_sales_pence.sum()) == gross
    assert int(tables["product_sales"].gross_sales_pence.sum()) == gross
    assert int(tables["orders"].sales_pence.sum()) == gross
    assert int(rfm.monetary_pence.sum()) == int(ledger.loc[identified&sales,"amount_pence"].sum())
    assert int(quality.rows.sum()) == len(raw)
    assert int(segments.customers.sum()) == len(rfm)
    assert cohorts.loc[cohorts.age.eq(0),"retention"].eq(1).all()
    assert cohorts.loc[cohorts.observed.eq(0),"retention"].isna().all()
    summary["validation"]={"reconciliations_passed":9,"sqlite_integrity":con.execute("PRAGMA integrity_check").fetchone()[0]}
    # Store SQL query evidence, not merely query templates.
    (ROOT/"reports/sql_validation.txt").write_text("SQL engine: SQLite "+sqlite3.sqlite_version+"\n"+json.dumps(summary["validation"],indent=2),encoding="utf-8")
    con.close()
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    # Aggregated country-month data supports consistent date and country dashboard filters.
    payload=dict(summary=summary,monthly=records(tables["monthly_sales"]),countryMonthly=records(tables["country_monthly"]),
                 countries=records(tables["country_sales"]),products=records(tables["product_sales"].head(20)),
                 segments=records(segments),cohorts=records(cohorts))
    (OUT/"dashboard_data.json").write_text(json.dumps(payload),encoding="utf-8")
    from deliverables import write_deliverables
    write_deliverables(ROOT,summary,payload)
    print(json.dumps({k:summary[k] for k in ["raw_rows","retained_rows","gross_sales_gbp","net_sales_gbp","identified_customers","repeat_customer_rate","validation"]},indent=2),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download",action="store_true")
    run(parser.parse_args().download)
