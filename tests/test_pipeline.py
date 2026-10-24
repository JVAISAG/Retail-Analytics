import json
import math
import sqlite3
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from pipeline import clean,cohort_table,repeat_study,rfm_customers,wilson


class CleaningTests(unittest.TestCase):
    def make(self,**kw):
        r=dict(source_sheet='test',source_row=2,invoice='100',stock_code='12345A',description='Item',quantity=2,invoice_date='2011-01-01 10:00:00',unit_price=1.25,customer_id=123,country='UK')
        r.update(kw)
        return r

    def test_returns_anonymous_duplicates_and_nonmerchandise(self):
        rows=[self.make(),self.make(source_row=3),self.make(invoice='C101',quantity=-1),
              self.make(invoice='102',customer_id=None),self.make(invoice='103',stock_code='POST'),
              self.make(invoice='104',unit_price=0),self.make(invoice='C105',quantity=1),
              self.make(invoice='106',quantity=0),self.make(invoice='107',invoice_date='bad')]
        ledger,quality,_=clean(pd.DataFrame(rows))
        q=quality.set_index('disposition').rows
        self.assertEqual(len(ledger),3)
        self.assertEqual(q['duplicate'],1)
        self.assertEqual(q.sum(),len(rows))
        self.assertEqual(ledger.amount_pence.sum(),375)
        self.assertEqual(ledger.customer_id.isna().sum(),1)
        self.assertEqual(ledger.loc[ledger.kind.eq('return'),'amount_pence'].iloc[0],-125)

    def test_pennies_and_fractional_quantity(self):
        ledger,q,_=clean(pd.DataFrame([self.make(unit_price=2.345),self.make(invoice='101',quantity=1.5)]))
        self.assertEqual(ledger.amount_pence.iloc[0],469)
        self.assertEqual(q.set_index('disposition').loc['invalid_required_value','rows'],1)

    def test_subpenny_unit_price_is_not_rounded_before_multiplication(self):
        ledger,_,_=clean(pd.DataFrame([self.make(unit_price=.001,quantity=1000)]))
        self.assertEqual(ledger.amount_pence.iloc[0],100)


class AnalyticsTests(unittest.TestCase):
    def test_wilson_known_interval(self):
        lo,hi=wilson(50,100)
        self.assertAlmostEqual(lo,0.40383153,places=7)
        self.assertAlmostEqual(hi,0.59616847,places=7)
        self.assertEqual(wilson(0,0),(None,None))

    def test_cohorts_distinguish_zero_and_unobserved(self):
        orders=pd.DataFrame([dict(customer_id='1',invoice='1',invoice_date='2011-01-02'),dict(customer_id='1',invoice='2',invoice_date='2011-03-02'),dict(customer_id='2',invoice='3',invoice_date='2011-02-03')])
        c=cohort_table(orders,pd.Timestamp('2011-03-09'))
        jan=c.loc[c.cohort.eq('2011-01')].set_index('age')
        self.assertEqual(jan.loc[0,'retention'],1)
        self.assertEqual(jan.loc[1,'retention'],0)
        self.assertTrue(pd.isna(jan.loc[2,'retention']))
        self.assertEqual(jan.loc[2,'observed'],0)

    def test_repeat_window_and_recent_customers(self):
        o=pd.DataFrame([
            dict(customer_id='1',invoice='1',invoice_date='2011-01-01',sales_pence=100),
            dict(customer_id='1',invoice='2',invoice_date='2011-04-01',sales_pence=100),
            dict(customer_id='2',invoice='3',invoice_date='2011-01-01',sales_pence=200),
            dict(customer_id='2',invoice='4',invoice_date='2011-04-02',sales_pence=100),
            dict(customer_id='3',invoice='5',invoice_date='2011-01-01',sales_pence=300),
            dict(customer_id='3',invoice='6',invoice_date='2011-01-01',sales_pence=50),
            dict(customer_id='4',invoice='7',invoice_date='2011-01-01',sales_pence=400),
            dict(customer_id='4',invoice='8',invoice_date='2011-02-01',sales_pence=100),
            dict(customer_id='5',invoice='9',invoice_date='2011-04-30',sales_pence=900)])
        eligible,study=repeat_study(o,pd.Timestamp('2011-05-01'))
        v=eligible.set_index('customer_id').repeat90
        self.assertTrue(v['1'])  # Exactly 90 days, inclusive.
        self.assertFalse(v['2']) # 91 days, excluded from outcome.
        self.assertFalse(v['3']) # Same timestamp is not subsequent.
        self.assertTrue(v['4'])
        self.assertEqual(study['excluded_recent_customers'],1)
        self.assertEqual(study['eligible_customers'],4)

    def test_rfm_ties_have_equal_scores_and_fixed_snapshot(self):
        o=pd.DataFrame([dict(customer_id=str(i),invoice=str(i),invoice_date='2011-01-01 12:00:00',sales_pence=100) for i in range(4)])
        r,s=rfm_customers(o,pd.Timestamp('2011-01-02 15:00:00'))
        self.assertEqual(str(s.date()),'2011-01-03')
        self.assertTrue(r.recency_days.eq(2).all())
        self.assertEqual(r.r_score.nunique(),1)
        self.assertEqual(r.f_score.nunique(),1)
        self.assertTrue(r.monetary_pence.eq(100).all())


@unittest.skipUnless((ROOT/'data/processed/retail.sqlite').exists(),'Run the pipeline for real-data checks')
class RealOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.con=sqlite3.connect(ROOT/'data/processed/retail.sqlite')
        cls.s=json.loads((ROOT/'data/processed/summary.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def scalar(self,sql):
        return self.con.execute(sql).fetchone()[0]

    def test_integrity_and_lineage(self):
        self.assertEqual(self.scalar('PRAGMA integrity_check'),'ok')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM ledger'),self.s['retained_rows'])
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM (SELECT source_sheet,source_row FROM ledger GROUP BY 1,2)'),self.s['retained_rows'])

    def test_invoice_headers_are_unambiguous(self):
        q="SELECT COUNT(*) FROM (SELECT invoice FROM ledger WHERE kind='sale' GROUP BY invoice HAVING COUNT(DISTINCT country)>1 OR COUNT(DISTINCT customer_id)>1 OR COUNT(DISTINCT order_date)>1)"
        self.assertEqual(self.scalar(q),0)

    def test_summary_reconciles_and_join_preserves_amount(self):
        gross=self.scalar("SELECT SUM(amount_pence) FROM ledger WHERE kind='sale'")
        self.assertEqual(gross,round(self.s['gross_sales_gbp']*100))
        self.assertAlmostEqual(self.s['average_order_value_gbp'],self.s['gross_sales_gbp']/self.s['orders'],places=8)
        self.assertEqual(self.scalar('SELECT SUM(net_sales_pence) FROM monthly_sales'),round(self.s['net_sales_gbp']*100))
        joined=self.scalar('SELECT SUM(o.sales_pence) FROM customer_orders o JOIN rfm_customers r ON r.customer_id=o.customer_id')
        self.assertEqual(joined,self.scalar('SELECT SUM(monetary_pence) FROM rfm_customers'))
        self.assertEqual(self.scalar('SELECT COUNT(DISTINCT customer_id) FROM customer_orders'),self.s['identified_customers'])

    def test_cohorts_and_study_denominators(self):
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM cohort_retention WHERE observed=0 AND retention IS NOT NULL'),0)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM cohort_retention WHERE retention<0 OR retention>1'),0)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM repeat_study_customers'),self.s['study']['eligible_customers'])
        for g in self.s['study']['groups']:
            n,s=self.con.execute('SELECT COUNT(*),SUM(repeat90) FROM repeat_study_customers WHERE "group"=?',(g['group'],)).fetchone()
            self.assertEqual(n,g['customers'])
            self.assertEqual(s,g['repeat_customers'])

    def test_dashboard_is_offline_and_populated(self):
        html=(ROOT/'dashboard.html').read_text(encoding='utf-8')
        self.assertNotIn('__DATA_JSON__',html)
        self.assertNotIn('<script src=',html)
        self.assertIn(str(self.s['raw_rows']),html)


if __name__=='__main__':
    unittest.main()
