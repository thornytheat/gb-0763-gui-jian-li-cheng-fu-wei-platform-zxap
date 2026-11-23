const statusLine = document.querySelector('#operation');

async function submit(path, payload) {
  const response = await fetch(path, {
    method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.message || '服务暂不可用');
  return result;
}

function handle(form, action) {
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button');
    button.disabled = true;
    statusLine.textContent = '正在核验…';
    try { await action(); }
    catch (error) { statusLine.textContent = error.message; }
    finally { button.disabled = false; }
  });
}

const save = document.querySelector('#save-run');
handle(save, async () => {
  const text = document.querySelector('#csv').value;
  const result = await submit('/api/runs', text ? {csv: text} : {sample: save.dataset.sample});
  const address = new URL('/work/issue', location.origin);
  address.search = new URLSearchParams({run: result.run_id, sample: save.dataset.sample});
  location.assign(address);
});

const issue = document.querySelector('#issue-run');
const download = document.querySelector('#download');
const picker = document.querySelector('#run');
picker?.addEventListener('change', () => {
  download.hidden = true;
  document.querySelector('#seal').textContent = '';
});
handle(issue, async () => {
  const run = picker.value;
  const result = await submit(`/api/runs/${run}/issue`, {});
  if (run !== picker.value) return;
  download.href = `/api/runs/${run}/export`;
  download.hidden = false;
  document.querySelector('#seal').textContent = result.seal;
  statusLine.textContent = result.reused ? '已取回原签发件' : '巡检证据已签发';
});
