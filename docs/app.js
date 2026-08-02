const integer = new Intl.NumberFormat('en-US');
const fixed = (value, digits) => Number(value).toFixed(digits);

fetch('data/phase1_first_batch_summary.json')
  .then((response) => {
    if (!response.ok) throw new Error('First-batch summary is unavailable.');
    return response.json();
  })
  .then((data) => {
    const batch = data.batch;
    const h2 = data.hypothesis_assessment.H2_conditional_hostility;
    const h4 = data.hypothesis_assessment.H4_minimum_operational_consensus;
    const monopoly = data.new_possibilities.find((item) => item.name === 'monopoly_survival_or_hegemonic_stability');

    document.getElementById('run-count').textContent = integer.format(batch.runs);
    document.getElementById('condition-count').textContent = integer.format(batch.conditions);
    document.getElementById('tick-count').textContent = `${fixed(batch.completed_ticks / 1_000_000, 2)}M`;
    document.getElementById('scarcity-attacks').textContent = fixed(h2.scarcity_minus_abundance_attack_count.mean, 2).replace('-', '−');
    document.getElementById('scarcity-collapse').textContent = `+${fixed(h2.scarcity_minus_abundance_collapse.mean, 3)}`;
    document.getElementById('single-survivor').textContent = `${fixed(monopoly.evidence.single_survivor_share_at_concentration_0_9 * 100, 2)}%`;
    document.getElementById('cooperation-effect').textContent = `+${fixed(h4.auditable_minus_none_cooperation.mean, 1)}`;
    document.getElementById('design-hash').textContent = `${batch.design_hash.slice(0, 12)}…`;
    document.getElementById('reconcile-count').textContent = `${integer.format(batch.resource_reconciled_runs)} / ${integer.format(batch.runs)} PASS`;
  })
  .catch((error) => {
    const notice = document.querySelector('.notice span');
    notice.textContent = `${notice.textContent} Generated JSON could not be loaded: ${error.message}`;
  });
