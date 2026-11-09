'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { DivinityEarthCircle } = require('../../frameworks/divinity-earth-circle');

test('Divinity–Earth Circle preserves the conscious center and multidirectional field', () => {
  const status = new DivinityEarthCircle().status();
  assert.equal(status.id, 'DIVINITY_EARTH_CIRCLE');
  assert.ok(status.center.includes('consciousness'));
  assert.equal(status.field, 'multidirectional_recursive_growth');
  assert.ok(status.movements.includes('outward_expansion'));
  assert.ok(status.movements.includes('return_feedback'));
});

test('Circle framework remains philosophical rather than a factual supernatural claim', () => {
  const status = new DivinityEarthCircle().status();
  assert.match(status.epistemic_scope, /not_a_claim_of_supernatural_mechanism/);
});
