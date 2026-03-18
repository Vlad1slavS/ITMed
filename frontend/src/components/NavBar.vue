<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <div class="logo">
        <span class="logo-mark">+</span>
        <span class="logo-text"
        >ItMed<span class="logo-dot">.</span></span
        >
      </div>
      <div class="nav-links">
        <a href="#top">Главная</a>
        <a href="#how-it-work">О системе</a>
        <a href="#tech">Технологии</a>
        <router-link to="/admin" class="nav-admin-link">Админка</router-link>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 0 2rem;
  height: 68px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border-subtle);
}

.navbar-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: var(--font-display);
  font-weight: 800;
  font-size: 1.2rem;
  color: var(--text-primary);
  margin-right: auto;
}

.logo-mark {
  width: 28px;
  height: 28px;
  background: var(--accent);
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
}

.logo-dot {
  color: var(--accent);
}

.nav-links {
  align-items: center;
  display: flex;
  gap: 2rem;
}

.nav-links a {
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 0.9rem;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: var(--text-primary);
}

.nav-admin-link {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface-2);
}

.nav-admin-link:hover {
  border-color: var(--accent);
  background: var(--accent-light);
}

.nav-status {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 99px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-muted);
}

.status-dot.online {
  background: var(--success);
  animation: pulse-ring 2s infinite;
}

.status-dot.offline {
  background: var(--danger);
}
</style>
