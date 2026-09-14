(() => {
  const menu = document.getElementById('moreMenu');
  if (!menu || typeof api !== 'function') return;
  if (document.getElementById('smsNav')) return;

  const item = document.createElement('button');
  item.id = 'smsNav';
  item.className = 'menu-item';
  item.textContent = '📱 پیامک';
  item.onclick = () => showSmsPage();
  menu.appendChild(item);

  window.showSmsPage = async function () {
    if (typeof showPage === 'function') showPage('sms');
    const root = document.getElementById('page-sms');
    if (!root) return;
    root.innerHTML = `<div class="page-header"><h2>📱 پیامک</h2><p>ارسال پیامک و مدیریت اعتبار</p></div>
      <div class="stats-grid"><div class="stat-card"><span>اعتبار پیامک</span><strong id="smsBalance">—</strong></div></div>
      <div class="card" style="margin-top:16px"><h3>ارسال پیامک</h3>
        <div class="form-grid"><input id="smsReceptor" placeholder="شماره گیرنده"><textarea id="smsMessage" rows="5" placeholder="متن پیام"></textarea></div>
        <button class="btn-primary" id="sendSmsBtn">ارسال پیامک</button><span id="smsResult" style="margin-right:12px"></span>
      </div>
      <div class="card" style="margin-top:16px"><h3>آخرین پیام‌ها</h3><div id="smsHistory">در حال بارگذاری...</div></div>`;

    try {
      const [balances, history] = await Promise.all([api('/api/credits'), api('/api/sms/history')]);
      document.getElementById('smsBalance').textContent = Number(balances.sms || 0).toLocaleString('fa-IR');
      const box = document.getElementById('smsHistory');
      box.innerHTML = history.length ? history.map(x => `<div style="padding:10px 0;border-bottom:1px solid #333"><b>${x.receptor}</b> — ${x.status === 'sent' ? 'ارسال شد' : 'ناموفق'}<br><small>${x.message}</small></div>`).join('') : 'هنوز پیامکی ارسال نشده است.';
    } catch (e) {
      document.getElementById('smsResult').textContent = e.message || 'خطا';
    }

    document.getElementById('sendSmsBtn').onclick = async () => {
      const result = document.getElementById('smsResult');
      result.textContent = 'در حال ارسال...';
      try {
        const data = await api('/api/sms/send', {method:'POST', body: JSON.stringify({receptor:document.getElementById('smsReceptor').value, message:document.getElementById('smsMessage').value})});
        result.textContent = `✓ ارسال شد | اعتبار باقی‌مانده: ${Number(data.balance || 0).toLocaleString('fa-IR')}`;
        showSmsPage();
      } catch (e) { result.textContent = e.message || 'ارسال ناموفق بود'; }
    };
  };
})();
