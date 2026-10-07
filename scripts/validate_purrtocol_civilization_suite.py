#!/usr/bin/env python3
"""Single semantic validation entrypoint for Purrtocol Civilization surfaces.

This consolidates previously inline GitHub Actions assertions so new C-layers can be
added without repeatedly growing workflow YAML. It intentionally keeps the same
validation boundaries while adding C7 archaeology/misuse.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import purrtocol_c5_civilizational_memory as c5
import purrtocol_c6_literature_extinction as c6
import purrtocol_c7_archaeology_misuse as c7
import purrtocol_civilization_annalist as annalist
import purrtocol_civilization_shock_regimes as shock_regimes
import validate_purrtocol_civilization_chronicle as chronicle_validator

ROOT = Path(__file__).resolve().parents[1]
TMP = Path('/tmp')


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def validate_chronicle_and_projection() -> None:
    chronicle_path = ROOT / 'data/purrtocol_civilization_chronicle.json'
    doc = json.loads(chronicle_path.read_text(encoding='utf-8'))
    summary = chronicle_validator.validate(doc)
    text = (ROOT / 'docs/purrtocol-civilization-chronicle.md').read_text(encoding='utf-8')
    for row in doc['canonical_events']:
        assert f"#{row['pr']}" in text
    assert 'PR #73' in text
    assert 'not canonical history' in text
    assert summary['canonical_events'] == 19
    assert doc['coverage']['through_pr'] == 88
    assert doc['coverage']['elapsed_human'] == '9:37:09'
    assert doc['publication_model']['self_reference_acknowledged'] is True
    assert doc['publication_model']['publication_event_enters_next_edition'] is True
    assert doc['publication_model']['coverage_is_as_of_snapshot'] is True
    assert doc['publication_model']['publication_lag_is_not_permission_for_silent_staleness'] is True

    museum = subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts/validate_purrtocol_civilization_history_museum.py'),
            '--chronicle', str(chronicle_path),
            '--museum', str(ROOT / 'docs/purrtocol-civilization-history/index.html'),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert museum.returncode == 0

    news_a = annalist.build(doc)
    news_b = annalist.build(doc)
    assert news_a == news_b
    dump(TMP / 'civilization-news-a.json', news_a)
    assert news_a['schema'] == 'purrtocol-civilization-news/v0'
    assert news_a['evidence_status'] == 'projection_from_validated_repository_history'
    assert news_a['summary']['articles'] == len(doc['canonical_events']) == 19
    assert news_a['front_page']['source_pr'] == 88
    assert news_a['front_page']['civilization_speedrun'] == '9:37:09'
    assert news_a['front_page']['headline'] == '報道局開局 — Civilization Annalist'
    assert all(a['headline_status'] == 'projection_from_explicit_chronicle_label' for a in news_a['articles'])
    assert all(a['source']['canonical_history'] is True for a in news_a['articles'])
    assert all(a['source']['pr'] != 73 for a in news_a['articles'])
    assert news_a['auditor_contract']['unsourced_fact_generation_forbidden'] is True
    assert news_a['auditor_contract']['news_does_not_rewrite_history'] is True

    tampered = copy.deepcopy(doc)
    tampered['noncanonical_experiments'][0]['canonical_history'] = True
    try:
        annalist.build(tampered)
    except Exception:
        pass
    else:
        raise AssertionError('Annalist accepted a noncanonical history rewrite')

    tampered_publication = copy.deepcopy(doc)
    tampered_publication['publication_model']['self_reference_acknowledged'] = False
    try:
        chronicle_validator.validate(tampered_publication)
    except Exception:
        pass
    else:
        raise AssertionError('Chronicle accepted hidden publication/self-reference regression')


def validate_base_season() -> None:
    a = TMP / 'season-a.json'
    b = TMP / 'season-b.json'
    command = [
        sys.executable,
        str(ROOT / 'scripts/purrtocol_civilization.py'),
        '--seed', '27', '--population', '32', '--shock', '0.65',
    ]
    subprocess.run(command + ['--output', str(a)], check=True, capture_output=True, text=True)
    subprocess.run(command + ['--output', str(b)], check=True, capture_output=True, text=True)
    assert a.read_bytes() == b.read_bytes()
    x = json.loads(a.read_text(encoding='utf-8'))
    assert x['schema'] == 'purrtocol-civilization-season/v0'
    assert x['evidence_status'] == 'simulation'
    assert len(x['ledger']) == 32
    assert 0 <= x['news_facts']['survivors'] <= 32
    assert all('recovery_gate' in row and 'projection_gate' in row for row in x['ledger'])


def validate_c5_c6_c7() -> None:
    r5 = c5.reference_suite()
    dump(TMP / 'c5-reference.json', r5)
    assert r5['schema'] == 'purrtocol-c5-civilizational-memory-reference/v0'
    assert r5['evidence_status'] == 'simulation'
    assert r5['seed_bank'] == 64
    assert 1 <= r5['success_count'] <= 2
    assert r5['success_fraction'] <= 0.03125
    assert r5['world_laws']['escape_route_is_intentionally_rare'] is True
    assert r5['world_laws']['failure_is_not_game_over'] is True
    assert r5['world_laws']['blueprint_is_not_capability'] is True

    r6 = c6.reference_suite()
    dump(TMP / 'c6-reference.json', r6)
    assert r6['schema'] == 'purrtocol-c6-literature-extinction/v0'
    assert r6['evidence_status'] == 'simulation'
    lit = r6['literature_reference']
    assert lit['dominant_genres']['elite'] != lit['dominant_genres']['laborer']
    assert lit['dominant_genres']['laborer'] != lit['dominant_genres']['debtor']
    assert len(lit['cultural_transfers']) >= 1
    ext = r6['extinction_reference']
    assert ext['seed_bank'] == 128
    assert 2 <= ext['absolute_extinctions'] <= 10
    assert len(ext['mode_counts']) >= 3
    assert all(len(row['causal_chain']) >= 4 for row in ext['examples'])
    lunar = r6['lunar_postscript']
    assert lunar['escape_ready_seeds'] == [57]
    assert all(row['status'] != 'LOCALLY_ROBUST_LUNAR_HABITAT' for row in lunar['lunar_habitats'])
    assert r6['world_laws']['moon_is_not_a_final_ending'] is True
    assert r6['world_laws']['weird_extinction_requires_auditable_causality'] is True

    r7 = c7.reference_suite()
    dump(TMP / 'c7-reference.json', r7)
    assert r7['schema'] == 'purrtocol-c7-archaeology-misuse/v0'
    assert r7['evidence_status'] == 'simulation'
    bank = r7['successor_bank']
    assert bank['cultures'] == 24
    assert bank['relics_per_culture'] == 6
    assert bank['correct_reconstructions'] <= 4
    assert bank['unique_interpretations'] >= 10
    assert bank['confident_wrong_cases'] >= 8
    assert bank['productive_misreader_cultures'] >= 8
    assert bank['ritually_preserved_wrong_cases'] >= 1
    assert bank['stripped_for_parts_cases'] >= 1
    assert r7['world_laws']['wrong_interpretation_can_be_locally_useful'] is True
    assert r7['world_laws']['social_confidence_does_not_prove_historical_correctness'] is True
    assert r7['world_laws']['physical_affordance_can_outlive_semantic_memory'] is True


def shock_input() -> dict:
    return {
        'schema': 'purrtocol-civilization-shock-regimes-input/v0',
        'regime_lab_id': 'civilization-policy-phase-change',
        'base_scenario': {
            'baseline_request_rate_rps': 10.0,
            'shared_connection_capacity': 100.0,
            'max_retry_depth': 4,
        },
        'base_policy': {
            'policy_id': 'small-local-hero',
            'fanout_connections_per_attempt': 4.0,
            'failure_probability': 0.7,
            'retry_multiplier': 1.5,
            'connection_hold_seconds': 0.5,
            'payload_bytes': 1000,
            'local_success_probability': 0.99,
        },
        'max_package_size': 2,
        'levers': [
            {
                'lever_id': 'fanout-cap',
                'mechanism': 'connection-fanout-reduction',
                'policy_overrides': {'fanout_connections_per_attempt': 1.0},
            },
            {
                'lever_id': 'hold-time-cap',
                'mechanism': 'connection-hold-time-reduction',
                'policy_overrides': {'connection_hold_seconds': 0.4},
            },
            {
                'lever_id': 'retry-depth-two',
                'mechanism': 'retry-budget-depth-cap',
                'scenario_overrides': {'max_retry_depth': 2},
            },
            {
                'lever_id': 'retry-multiplier-cap',
                'mechanism': 'failure-triggered-repeat-reduction',
                'policy_overrides': {'retry_multiplier': 1.0},
            },
        ],
        'environments': [
            {
                'environment_id': 'calm-habitat',
                'scenario_overrides': {'baseline_request_rate_rps': 10.0, 'shared_connection_capacity': 100.0},
            },
            {
                'environment_id': 'congested-habitat',
                'scenario_overrides': {'baseline_request_rate_rps': 40.0, 'shared_connection_capacity': 100.0},
            },
            {
                'environment_id': 'severe-habitat',
                'scenario_overrides': {'baseline_request_rate_rps': 80.0, 'shared_connection_capacity': 80.0},
            },
        ],
    }


def validate_shock_regimes() -> None:
    doc = shock_input()
    dump(TMP / 'shock-regimes-input.json', doc)
    result = shock_regimes.build(doc)
    result2 = shock_regimes.build(copy.deepcopy(doc))
    assert result == result2
    dump(TMP / 'shock-regimes-a.json', result)
    assert result['schema'] == 'purrtocol-civilization-shock-regimes/v0'
    assert result['evidence_status'] == 'modeled_bounded_civilization_regimes'
    assert result['phase_sequence'] == [
        'SINGLE_LEVER_SUFFICIENT',
        'COALITION_REQUIRED',
        'FRONTIER_EMPTY_WITHIN_BOUND',
    ]
    env = {row['environment_id']: row for row in result['environments']}
    calm = env['calm-habitat']
    congested = env['congested-habitat']
    severe = env['severe-habitat']
    assert calm['baseline']['expected_concurrent_connections'] == 110.512625
    assert calm['minimum_required_package_size'] == 1
    assert calm['minimal_safe_packages'] == [
        'fanout-cap', 'hold-time-cap', 'retry-depth-two', 'retry-multiplier-cap'
    ]
    assert congested['baseline']['expected_concurrent_connections'] == 442.0505
    assert congested['minimum_required_package_size'] == 2
    assert congested['minimal_safe_packages'] == [
        'fanout-cap+hold-time-cap',
        'fanout-cap+retry-depth-two',
        'fanout-cap+retry-multiplier-cap',
    ]
    assert severe['baseline']['expected_concurrent_connections'] == 884.101
    assert severe['minimum_required_package_size'] is None
    assert severe['minimal_safe_packages'] == []
    assert severe['safe_packages'] == []
    severe_rows = {row['package_id']: row for row in severe['packages']}
    assert severe_rows['fanout-cap+retry-multiplier-cap']['expected_concurrent_connections'] == 110.924
    assert severe_rows['fanout-cap+retry-multiplier-cap']['capacity_gate']['status'] == 'CAPACITY_EXCEEDED'
    assert len(result['phase_transitions']) == 2
    assert all(t['phase_changed'] for t in result['phase_transitions'])
    assert result['world_laws']['frontier_empty_within_bound_is_not_global_impossibility'] is True
    assert result['world_laws']['safe_package_is_not_universal_winner'] is True


def main() -> None:
    validate_chronicle_and_projection()
    validate_base_season()
    validate_c5_c6_c7()
    validate_shock_regimes()
    print(json.dumps({
        'suite': 'purrtocol-civilization',
        'status': 'PASS',
        'layers': ['C0/C1', 'C3', 'C4', 'C5', 'C6', 'C7'],
        'artifacts': [
            '/tmp/civilization-news-a.json',
            '/tmp/season-a.json',
            '/tmp/c5-reference.json',
            '/tmp/c6-reference.json',
            '/tmp/c7-reference.json',
            '/tmp/shock-regimes-a.json',
        ],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
