document.addEventListener('DOMContentLoaded', () => {
  if (!document.cookie.includes('gr_session=')) {
    const here = location.pathname;
    if (here.length > 1 && here.startsWith('/grs_')) {
      location.replace(here.endsWith('/') ? here : here + '/');
    }
  }
});
