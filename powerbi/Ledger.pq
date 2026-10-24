// Create a blank query, paste in Advanced Editor, set ProjectRoot, and name it Ledger.
let
    ProjectRoot = "C:\REPLACE_WITH_PROJECT_FOLDER\retail-analytics",
    Source = Binary.Decompress(File.Contents(ProjectRoot & "\data\processed\ledger.csv.gz"), Compression.GZip),
    Parsed = Csv.Document(Source, [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Parsed, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {
        {"source_sheet", type text}, {"source_row", Int64.Type},
        {"invoice", type text}, {"stock_code", type text}, {"description", type text},
        {"quantity", Int64.Type}, {"invoice_date", type datetime},
        {"order_date", type date}, {"month", type text},
        {"unit_price_gbp", type number}, {"amount_pence", Int64.Type},
        {"customer_id", type text}, {"country", type text}, {"kind", type text}
    }, "en-GB"),
    MissingCustomers = Table.ReplaceValue(Types,"",null,Replacer.ReplaceValue,{"customer_id"})
in
    MissingCustomers
