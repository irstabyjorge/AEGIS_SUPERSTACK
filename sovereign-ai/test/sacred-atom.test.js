'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { SacredAtomEngine, SACRED_ATOM_SPEC } = require('../../frameworks/sacred-atom');

test('Sacred Atom reports configured, knowledge-only state', () => {
  const status = new SacredAtomEngine().status();
  assert.equal(status.id, 'SACRED_ATOM');
  assert.equal(status.state, 'configured');
  assert.equal(status.mode, 'knowledge_only');
  assert.equal(status.boundaries.executes_source_code, false);
  assert.ok(status.layers.includes('neuroplasticity'));
});

test('Sacred Atom accepts complete provenance envelope', () => {
  const result = new SacredAtomEngine().validateEnvelope({
    input: { claim: 'example' },
    authorized_transformation: 'summarize_and_compare',
    output: { summary: 'example' },
    provenance: { source_id: 'test-fixture', status: 'synthetic_test' }
  });
  assert.deepEqual(result, { valid: true, errors: [] });
});

test('Sacred Atom rejects missing provenance and executable transformation values', () => {
  const result = new SacredAtomEngine().validateEnvelope({
    input: 'x',
    authorized_transformation: { code: 'not-accepted' },
    output: 'y'
  });
  assert.equal(result.valid, false);
  assert.ok(result.errors.includes('missing_provenance'));
  assert.ok(result.errors.includes('authorized_transformation_must_be_a_label_not_executable_code'));
});

test('TAUROS-100K remains conceptual and does not claim mesh execution', () => {
  assert.equal(SACRED_ATOM_SPEC.geometry.tauros_100k.status, 'conceptual_simulation_only');
  assert.equal(SACRED_ATOM_SPEC.geometry.tauros_100k.validation_passes_executed, 0);
});
