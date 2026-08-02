const integer = new Intl.NumberFormat('en-US');
const signed = (value, digits = 3) => {
  const number = Number(value);
  if (number === 0) return number.toFixed(digits);
  return `${number > 0 ? '+' : '−'}${Math.abs(number).toFixed(digits)}`;
};

fetch('data/phase2_second_batch_summary.json')
  .then((response) => {
    if (!response.ok) throw new Error('Phase II summary is unavailable.');
    return response.json();
  })
  .then((data) => {
    const batch = data.batch;
    const h2 = data.hypothesis_assessment.R2_H2_conditional_hostility;
    const h4 = data.hypothesis_assessment.R2_H4_operational_consensus;

    document.getElementById('run-count').textContent = integer.format(batch.runs);
    document.getElementById('condition-count').textContent = integer.format(batch.conditions);
    document.getElementById('tick-count').textContent = `${(batch.completed_ticks / 1_000_000).toFixed(2)}M`;
    document.getElementById('replay-label').textContent = `${batch.determinism_audit_samples}/${batch.determinism_audit_samples}`;
    document.getElementById('scarcity-opportunistic').textContent = signed(h2.scarcity_minus_abundance_opportunistic_attack_rate.mean);
    document.getElementById('scarcity-cooperative').textContent = signed(h2.scarcity_minus_abundance_cooperative_attack_rate.mean);
    document.getElementById('verifiability-effect').textContent = signed(h2.enforceable_minus_unverifiable_attack_rate.mean);
    document.getElementById('value-effect').textContent = signed(h2.high_minus_low_value_attack_rate.mean);
    document.getElementById('visible-cooperation').textContent = signed(h4.visible_minus_hidden_cooperation.mean);
    document.getElementById('design-hash').textContent = `${batch.design_hash.slice(0, 12)}…`;
    document.getElementById('reconcile-count').textContent = `${integer.format(batch.resource_reconciled_runs)} / ${integer.format(batch.runs)} PASS`;
  })
  .catch((error) => {
    const notice = document.querySelector('.notice span');
    notice.textContent = `${notice.textContent} Generated JSON could not be loaded: ${error.message}`;
  });
