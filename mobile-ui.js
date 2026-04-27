(function () {
  const scriptUrl = new URL(document.currentScript.src);
  const rootUrl = new URL(".", scriptUrl);

  const links = [
    ["Home", "⌂", "index.html"],
    ["Events", "🎤", "years.html"],
    ["Books", "📚", "books/index_page01.html"],
    ["Films", "🎬", "films/index.html"],
    ["Literature", "✍️", "literature/index.html"]
  ];

  function makeUrl(path) {
    return new URL(path, rootUrl).href;
  }

  function addBottomNav() {
    if (document.querySelector(".mobile-bottom-nav")) {
      return;
    }

    const currentPath = window.location.pathname.replace(/\\/g, "/");
    const rootIndexPath = new URL("index.html", rootUrl).pathname.replace(/\\/g, "/");
    const nav = document.createElement("nav");
    nav.className = "mobile-bottom-nav";
    nav.setAttribute("aria-label", "Mobile navigation");

    links.forEach(([label, icon, href]) => {
      const link = document.createElement("a");
      link.href = makeUrl(href);
      link.innerHTML = "<span aria-hidden=\"true\">" + icon + "</span>" + label;

      if (currentPath.endsWith("/" + href) || (href === "index.html" && currentPath === rootIndexPath)) {
        link.setAttribute("aria-current", "page");
      }

      nav.appendChild(link);
    });

    document.body.appendChild(nav);
  }

  function addBackToTop() {
    if (document.querySelector(".back-to-top")) {
      return;
    }

    const button = document.createElement("button");
    button.className = "back-to-top";
    button.type = "button";
    button.setAttribute("aria-label", "Back to top");
    button.textContent = "↑";

    button.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    window.addEventListener("scroll", () => {
      button.classList.toggle("is-visible", window.scrollY > 500);
    }, { passive: true });

    document.body.appendChild(button);
  }

  function wrapMobileGalleries() {
    document.querySelectorAll(".page").forEach((page) => {
      let group = [];

      function flush() {
        if (group.length < 3) {
          group = [];
          return;
        }

        const wrapper = document.createElement("div");
        wrapper.className = "mobile-gallery";
        group[0].before(wrapper);
        group.forEach((img) => wrapper.appendChild(img));
        group = [];
      }

      Array.from(page.childNodes).forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE && node.tagName === "IMG") {
          group.push(node);
          return;
        }

        if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() === "") {
          return;
        }

        flush();
      });

      flush();
    });
  }

  function findPageLink(direction) {
    const navLinks = Array.from(document.querySelectorAll(".navigation .nav-btn[href]"));

    if (direction === "next") {
      return navLinks.find((link) => /next/i.test(link.textContent)) || null;
    }

    return navLinks.find((link) => /previous|prev/i.test(link.textContent))
      || navLinks.find((link) => /back/i.test(link.textContent))
      || navLinks[0]
      || null;
  }

  function addSwipeNavigation() {
    let startX = 0;
    let startY = 0;
    let startTime = 0;

    document.addEventListener("touchstart", (event) => {
      if (event.touches.length !== 1) {
        return;
      }

      startX = event.touches[0].clientX;
      startY = event.touches[0].clientY;
      startTime = Date.now();
    }, { passive: true });

    document.addEventListener("touchend", (event) => {
      if (!startTime || event.changedTouches.length !== 1) {
        return;
      }

      const endX = event.changedTouches[0].clientX;
      const endY = event.changedTouches[0].clientY;
      const deltaX = endX - startX;
      const deltaY = endY - startY;
      const elapsed = Date.now() - startTime;

      startTime = 0;

      if (elapsed > 900 || Math.abs(deltaX) < 80 || Math.abs(deltaY) > 70 || Math.abs(deltaX) < Math.abs(deltaY) * 1.6) {
        return;
      }

      const target = findPageLink(deltaX < 0 ? "next" : "back");
      if (target) {
        window.location.href = target.href;
      }
    }, { passive: true });
  }

  document.addEventListener("DOMContentLoaded", () => {
    const currentPath = window.location.pathname.replace(/\\/g, "/");
    const rootIndexPath = new URL("index.html", rootUrl).pathname.replace(/\\/g, "/");
    document.body.classList.toggle("home-page", currentPath === rootIndexPath);
    addBottomNav();
    addBackToTop();
    wrapMobileGalleries();
    addSwipeNavigation();
  });
}());
