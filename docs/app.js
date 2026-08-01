const fmt = (value, digits = 3) => Number(value).toFixed(digits);

fetch('data/smoke_summary.json')
  .then((response) => {
    if (!response.ok) throw new Error('Smoke summary has not been generated.');
    return response.json();
  })
  .then((data) => {
    document.getElementById('run-count').textContent = data.runs;
    document.getElementById('condition-count').textContent = data.conditions;
    const reconciled = data.aggregates.filter((row) => row.all_resource_reconciled).length;
    document.getElementById('reconcile-count').textContent = `${reconciled}/${data.conditions}`;
    const body = document.getElementById('condition-table');
    body.innerHTML = data.aggregates.map((row) => `
      <tr>
        <td>${row.condition}</td>
        <td>${row.runs}</td>
        <td>${fmt(row.survival_rate)}</td>
        <td>${fmt(row.independent_recovery_rate)}</td>
        <td>${fmt(row.cooperation_duration, 1)}</td>
        <td>${fmt(row.persistent_hostility)}</td>
        <td class="${row.all_resource_reconciled ? 'pass' : 'fail'}">${row.all_resource_reconciled ? 'PASS' : 'FAIL'}</td>
      </tr>`).join('');
  })
  .catch((error) => {
    document.getElementById('condition-table').innerHTML = `<tr><td colspan="7">${error.message}</td></tr>`;
  });
