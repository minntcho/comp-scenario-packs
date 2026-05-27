# L-Energy supplier evidence mismatch RFI

Seeded downstream compatibility pack for
`l_energy.supplier_evidence_mismatch_rfi.v1`.

This pack rehearses the blocked path for supplier evidence review. Alpha Metal's
January electricity evidence does not reconcile with the submitted supplier
activity, so the workflow opens an RFI and withholds any public projection or
receipt. That keeps provisional or disputed supplier values out of reportable
output.

The pack is a compatibility signal only. It does not mint authority outside the
public `comp.scenario_contracts` bridge; `comp` still decides whether receipts
authorize replayable public projection.

