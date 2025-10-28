// Reusable banner to allow switching between Admin and Customer portals
(function(){
  function createBanner(defaultRole){
    if (!document.body) return;
    const existing = document.getElementById('nexus-switch-banner');
    if (existing) return;

    const banner = document.createElement('div');
    banner.id = 'nexus-switch-banner';
    banner.style.position = 'fixed';
    banner.style.top = '0';
    banner.style.left = '0';
    banner.style.right = '0';
    banner.style.zIndex = '9999';
    banner.style.background = 'linear-gradient(90deg,#667eea,#764ba2)';
    banner.style.color = 'white';
    banner.style.padding = '8px 16px';
    banner.style.display = 'flex';
    banner.style.alignItems = 'center';
    banner.style.justifyContent = 'space-between';

    const msg = document.createElement('div');
    msg.innerHTML = `<strong>Signed in</strong> — Switch to:`;

    const actions = document.createElement('div');
    const adminBtn = document.createElement('button');
    adminBtn.textContent = 'Admin Dashboard';
    adminBtn.style.marginRight = '8px';
    const customerBtn = document.createElement('button');
    customerBtn.textContent = 'Customer Portal';

    [adminBtn, customerBtn].forEach(b=>{
      b.style.border = 'none';
      b.style.padding = '6px 10px';
      b.style.borderRadius = '6px';
      b.style.cursor = 'pointer';
      b.style.background = 'rgba(255,255,255,0.12)';
      b.style.color = 'white';
    });

    adminBtn.onclick = function(){
      // route to admin
      const token = sessionStorage.getItem('access_token');
      if (token) {
        window.location.href = '/admin/';
      } else {
        window.location.href = '/login.html';
      }
    };

    customerBtn.onclick = function(){
      const token = sessionStorage.getItem('access_token');
      if (token) {
        window.location.href = '/customer/';
      } else {
        window.location.href = '/login.html';
      }
    };

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.marginLeft = '12px';
    closeBtn.style.background = 'transparent';
    closeBtn.style.border = 'none';
    closeBtn.style.color = 'white';
    closeBtn.style.fontSize = '20px';
    closeBtn.style.cursor = 'pointer';
    closeBtn.onclick = function(){ banner.remove(); };

    actions.appendChild(adminBtn);
    actions.appendChild(customerBtn);
    actions.appendChild(closeBtn);

    banner.appendChild(msg);
    banner.appendChild(actions);
    document.body.style.paddingTop = '48px';
    document.body.insertBefore(banner, document.body.firstChild);
  }

  // Auto-initialize when loaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ()=>createBanner());
  } else {
    createBanner();
  }
})();
