(function () {
  let startX = 0;
  let startY = 0;
  let startTime = 0;

  function isTouchDevice() {
    return "ontouchstart" in window || navigator.maxTouchPoints > 0;
  }

  function getNavigationLinks() {
    return Array.from(document.querySelectorAll(".navigation a[href], .nav-btn[href]"));
  }

  function findLink(direction) {
    const links = getNavigationLinks();

    if (direction === "next") {
      return links.find((link) => /next/i.test(link.textContent)) || null;
    }

    return links.find((link) => /previous|prev/i.test(link.textContent))
      || links.find((link) => /back/i.test(link.textContent))
      || links[0]
      || null;
  }

  function shouldIgnoreSwipe(event) {
    const target = event.target;
    return target.closest && target.closest("a, button, input, textarea, select, video, audio");
  }

  function handleTouchStart(event) {
    if (event.touches.length !== 1 || shouldIgnoreSwipe(event)) {
      startTime = 0;
      return;
    }

    startX = event.touches[0].clientX;
    startY = event.touches[0].clientY;
    startTime = Date.now();
  }

  function handleTouchEnd(event) {
    if (!startTime || event.changedTouches.length !== 1) {
      return;
    }

    const endX = event.changedTouches[0].clientX;
    const endY = event.changedTouches[0].clientY;
    const deltaX = endX - startX;
    const deltaY = endY - startY;
    const elapsed = Date.now() - startTime;

    startTime = 0;

    if (elapsed > 900) {
      return;
    }

    if (Math.abs(deltaX) < 80 || Math.abs(deltaY) > 70 || Math.abs(deltaX) < Math.abs(deltaY) * 1.6) {
      return;
    }

    const link = findLink(deltaX < 0 ? "next" : "back");
    if (link) {
      window.location.href = link.href;
    }
  }

  if (isTouchDevice()) {
    document.addEventListener("touchstart", handleTouchStart, { passive: true });
    document.addEventListener("touchend", handleTouchEnd, { passive: true });
  }
}());
