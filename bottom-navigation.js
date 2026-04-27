(function () {
  const scriptUrl = new URL(document.currentScript.src);
  const rootUrl = new URL(".", scriptUrl);

  const navItems = [
    ["Home", "🏠", "index.html"],
    ["Events", "🎤", "years.html"],
    ["Books", "📚", "books/index_page01.html"],
    ["Films", "🎬", "films/index.html"],
    ["Travel", "🌍", "travel/index.html"],
    ["Science", "🔬", "science/index.html"],
    ["Literature", "✍️", "literature/index.html"]
  ];

  function makeUrl(path) {
    return new URL(path, rootUrl).href;
  }

  function injectStyles() {
    if (document.getElementById("mobile-bottom-nav-styles")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "mobile-bottom-nav-styles";
    style.textContent = `
      @media (max-width: 700px) {
        body {
          padding-bottom: 72px;
        }

        .mobile-bottom-nav {
          position: fixed;
          left: 0;
          right: 0;
          bottom: 0;
          z-index: 1000;
          background: rgba(255, 255, 255, 0.97);
          border-top: 1px solid rgba(0, 0, 0, 0.12);
          box-shadow: 0 -4px 16px rgba(0, 0, 0, 0.14);
          backdrop-filter: blur(8px);
          overflow: hidden;
        }

        .mobile-bottom-nav-track {
          display: flex;
          gap: 4px;
          min-height: 58px;
          padding: 5px 8px 7px;
          overflow-x: auto;
          overscroll-behavior-x: contain;
          scroll-snap-type: x proximity;
          scrollbar-width: none;
          -webkit-overflow-scrolling: touch;
        }

        .mobile-bottom-nav-track::-webkit-scrollbar {
          display: none;
        }

        .mobile-bottom-nav a {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          flex: 0 0 58px;
          gap: 2px;
          min-height: 48px;
          padding: 3px 4px;
          border-radius: 9px;
          color: #394143;
          text-decoration: none;
          font-family: Georgia, serif;
          font-size: 10px;
          font-weight: 700;
          line-height: 1.1;
          scroll-snap-align: center;
          white-space: nowrap;
          -webkit-tap-highlight-color: transparent;
        }

        .mobile-bottom-nav span {
          font-size: 17px;
          line-height: 1;
        }

        .mobile-bottom-nav a[aria-current="page"] {
          color: #2c7a7b;
          background: #eef6f6;
        }

        .mobile-bottom-nav a:active {
          background: #eef6f6;
        }
      }

      @media (min-width: 701px) {
        .mobile-bottom-nav {
          display: none;
        }
      }
    `;

    document.head.appendChild(style);
  }

  function addBottomNav() {
    if (document.querySelector(".mobile-bottom-nav")) {
      return;
    }

    const currentPath = window.location.pathname.replace(/\\/g, "/");
    const nav = document.createElement("nav");
    const track = document.createElement("div");
    nav.className = "mobile-bottom-nav";
    nav.setAttribute("aria-label", "Mobile navigation");
    track.className = "mobile-bottom-nav-track";

    navItems.forEach(([label, icon, href]) => {
      const link = document.createElement("a");
      const targetUrl = makeUrl(href);
      const targetPath = new URL(targetUrl).pathname.replace(/\\/g, "/");

      link.href = targetUrl;
      link.innerHTML = "<span aria-hidden=\"true\">" + icon + "</span>" + label;

      if (currentPath === targetPath || currentPath.endsWith("/" + href)) {
        link.setAttribute("aria-current", "page");
      }

      track.appendChild(link);
    });

    nav.appendChild(track);
    document.body.appendChild(nav);

    const activeLink = nav.querySelector("[aria-current='page']");
    if (activeLink) {
      activeLink.scrollIntoView({ inline: "center", block: "nearest" });
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    injectStyles();
    addBottomNav();
  });
}());
