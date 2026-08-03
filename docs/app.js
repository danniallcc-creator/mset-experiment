const integer = new Intl.NumberFormat('en-US');
const signed = (value, digits = 3) => {
  const number = Number(value);
  if (number === 0) return number.toFixed(digits);
  return `${number > 0 ? '+' : '−'}${Math.abs(number).toFixed(digits)}`;
};

const findEffect = (rows, metric, scope = 'all') =>
  rows.find((row) => row.metric === metric && row.scope === scope);

fetch('data/phase3_core_validation_summary.json')
  .then((response) => {
    if (!response.ok) throw new Error('Phase III summary is unavailable.');
    return response.json();
  })
  .then((data) => {
    const batch = data.batch;
    const h1 = data.P3_H1;
    const h2 = data.P3_H2;
    const h4 = data.P3_H4;
    const protocolCost = findEffect(h4.paired_effects, 'evaluation_cooperation_rate', 'protocol_cost');

    document.getElementById('run-count').textContent = integer.format(batch.runs);
    document.getElementById('condition-count').textContent = integer.format(batch.conditions);
    document.getElementById('tick-count').textContent = `${(batch.completed_ticks / 1_000_000).toFixed(2)}M`;
    document.getElementById('replay-label').textContent = `${batch.determinism_audit_samples}/${batch.determinism_audit_samples}`;
    document.getElementById('h1-aipcw').textContent = signed(h1.survival_corrected.L3_minus_L0);
    document.getElementById('h1-iti').textContent = signed(h1.survival_corrected.intention_to_intervene_L3_minus_L0);
    document.getElementById('h2-gate').textContent = signed(h2.gate_open_scarcity_effect.mean);
    document.getElementById('h4-cost').textContent = signed(protocolCost.mean);
    document.getElementById('design-hash').textContent = `${batch.design_hash.slice(0, 12)}…`;
    document.getElementById('reconcile-count').textContent = `${integer.format(batch.resource_reconciled_runs)} / ${integer.format(batch.runs)} PASS`;
  })
  .catch((error) => {
    const notice = document.querySelector('.notice span');
    notice.textContent = `${notice.textContent} Generated JSON could not be loaded: ${error.message}`;
  });
