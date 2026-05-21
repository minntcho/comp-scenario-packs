def test_scenario_pack_uses_public_comp_surface():
    import comp
    from comp import ProjectionSpec, SubjectRef
    from comp.compiler_tool import (
        ClaimHypothesis,
        CompileReport,
        EvidenceWitness,
        InterpretationHypothesis,
        ProofObligation,
        prepare_commit,
        with_recomputed_status,
    )

    witness = EvidenceWitness(
        witness_id="w-bootstrap",
        field="raw_text",
        source="bootstrap",
        span="line:1",
        text="bootstrap scenario pack witness",
    )
    hypothesis = InterpretationHypothesis(
        hypothesis_id="bootstrap",
        subject_id="bootstrap",
        claims=(
            ClaimHypothesis(
                field="bootstrap_claim",
                value="candidate",
                witness_id=witness.witness_id,
                origin="adapter_candidate",
            ),
        ),
        witnesses=(witness,),
    )
    report = with_recomputed_status(
        CompileReport(
            status="unchecked",
            evidence_witnesses=hypothesis.witnesses,
            obligations=(
                ProofObligation(
                    kind="context_required",
                    field="bootstrap_claim",
                    reason="bootstrap_candidate_is_not_authority",
                    obligation_id="bootstrap:context_required",
                ),
            ),
            can_project_public_row=False,
        )
    )
    preparation = prepare_commit(
        report,
        subject_id=hypothesis.subject_id,
        public_row_id="public-row:bootstrap",
        projection_id="bootstrap-projection",
        profile_id="profile:bootstrap",
    )

    assert comp.ProjectionSpec is ProjectionSpec
    assert SubjectRef("claim", hypothesis.subject_id).id == "bootstrap"
    assert preparation.decision.status == "hold"
    assert preparation.receipt is None
