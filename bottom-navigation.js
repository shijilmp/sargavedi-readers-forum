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

  /* ---------- Desktop only (>= 901px): masthead, category menu, footer, article sidebar, photo grid, image viewer ---------- */

  const isDesktop = () => window.matchMedia("(min-width: 901px)").matches;

  const catItems = [
    ["ഹോം", "index.html"],
    ["സർഗ്ഗവേദിയെക്കുറിച്ച്", "about.html"],
    ["ചരിത്രം", "history.html"],
    ["വീട്ടുമുറ്റ ചർച്ച", "veettumuttam.html"],
    ["പുരസ്കാരങ്ങൾ", "awards.html"],
    ["എഴുത്തുകാരും അതിഥികളും", "people.html"],
    ["മാധ്യമങ്ങളിൽ സർഗവേദി", "media.html"]
  ];

  const archiveItems = [
    ["പരിപാടികൾ – വർഷം തിരിച്ച്", "years.html"],
    ["പുസ്തകങ്ങൾ", "books/index_page01.html"],
    ["സിനിമ", "films/index.html"],
    ["നാടകം", "drama/index.html"],
    ["സാഹിത്യം", "literature/index.html"],
    ["ശാസ്ത്രം", "science/index.html"],
    ["യാത്ര", "travel/index.html"]
  ];

  const footerColumns = [
    ["ഫോറത്തെ അറിയാൻ", [["സർഗ്ഗവേദിയെക്കുറിച്ച്", "about.html"], ["ചരിത്രം", "history.html"], ["വീട്ടുമുറ്റ ചർച്ചകൾ", "veettumuttam.html"], ["പുരസ്കാരങ്ങൾ", "awards.html"], ["എഴുത്തുകാരും അതിഥികളും", "people.html"], ["മാധ്യമങ്ങളിൽ സർഗവേദി", "media.html"]]],
    ["പരിപാടികൾ", [["എല്ലാ പരിപാടികളും (വർഷം തിരിച്ച്)", "years.html"], ["2026", "2026/index.html"], ["2024 – 2025", "before2026/index.html"], ["2018 – 2024", "before2026/index_01.html"], ["2006 – 2017", "before2026/index_02.html"]]],
    ["വായനയും എഴുത്തും", [["പുസ്തക നിരൂപണങ്ങൾ", "books/Books/index_page01.html"], ["ലോക പ്രശസ്ത എഴുത്തുകാർ", "books/Writters/world-writers.html"], ["സിനിമ", "films/index.html"], ["നാടകം", "drama/index.html"], ["ശാസ്ത്രം", "science/index.html"], ["കഥകളും കവിതകളും", "literature/index.html"], ["യാത്ര", "travel/index.html"]]]
  ];

  function injectDesktopStyles() {
    if (document.getElementById("desktop-ui-styles")) {
      return;
    }

    const style = document.createElement("style");
    style.id = "desktop-ui-styles";
    style.textContent = `
      @media (min-width: 901px) {
        .zoomable { cursor: zoom-in; }

        .lightbox {
          position: fixed;
          inset: 0;
          z-index: 2000;
          display: none;
          align-items: center;
          justify-content: center;
          background: rgba(10, 18, 19, 0.92);
        }

        .lightbox.open { display: flex; }

        .lightbox img {
          max-width: 88vw;
          max-height: 86vh;
          border-radius: 6px;
          box-shadow: 0 8px 40px rgba(0, 0, 0, 0.5);
        }

        .lightbox button {
          position: absolute;
          border: 0;
          background: rgba(255, 255, 255, 0.14);
          color: #fff;
          font-size: 30px;
          line-height: 1;
          width: 48px;
          height: 48px;
          border-radius: 50%;
          cursor: pointer;
        }

        .lightbox button:hover { background: rgba(255, 255, 255, 0.28); }
        .lightbox-close { top: 18px; right: 22px; }
        .lightbox-prev { left: 22px; top: 50%; transform: translateY(-50%); }
        .lightbox-next { right: 22px; top: 50%; transform: translateY(-50%); }

        .lightbox-count {
          position: absolute;
          bottom: 16px;
          left: 50%;
          transform: translateX(-50%);
          color: #fff;
          font: 14px Georgia, serif;
          opacity: 0.8;
        }
      }
    `;

    document.head.appendChild(style);
  }

  function pathOf(href) {
    return new URL(makeUrl(href)).pathname;
  }

  function isCurrentSection(href) {
    const here = window.location.pathname.replace(/\\/g, "/");
    const target = pathOf(href);
    if (here === target || here + "index.html" === target) {
      return true;
    }
    if (href === "years.html") {
      return /\/(2026|before2026)\//.test(here);
    }
    if (href === "books/index_page01.html") {
      return /\/books\//.test(here);
    }
    if (href === "index.html") {
      return here === target || here === new URL(".", makeUrl("index.html")).pathname;
    }
    return false;
  }

  function addMasthead() {
    if (document.querySelector(".site-top")) {
      return;
    }

    let today = "";
    try {
      today = new Date().toLocaleDateString("ml-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
    } catch (e) {
      today = new Date().toDateString();
    }

    const top = document.createElement("div");
    top.className = "site-top";
    top.innerHTML =
      "<div class=\"utility\"><div class=\"util-inner\"><span>" + today + " · ആലക്കോട്, കണ്ണൂർ</span>" +
      "<span class=\"util-links\"><a href=\"" + makeUrl("about.html") + "\">സർഗ്ഗവേദിയെക്കുറിച്ച്</a>" +
      "<a href=\"" + makeUrl("history.html") + "\">ചരിത്രം</a></span></div></div>" +
      "<div class=\"masthead\"><a class=\"mast-logo\" href=\"" + makeUrl("index.html") + "\">" +
      "<img src=\"" + makeUrl("logo.svg") + "\" alt=\"\" width=\"76\" height=\"76\">" +
      "<span class=\"mast-text\"><span class=\"mast-title\" role=\"img\" aria-label=\"സർഗവേദി\"></span>" +
      "<span class=\"mast-sub\">റീഡേഴ്സ് ഫോറം · ആലക്കോട്</span></span></a></div>";

    const nav = document.createElement("nav");
    nav.className = "catnav";
    nav.setAttribute("aria-label", "Main navigation");
    const inner = document.createElement("div");
    inner.className = "cat-inner";

    catItems.forEach(([label, href]) => {
      const link = document.createElement("a");
      link.href = makeUrl(href);
      link.textContent = label;
      if (isCurrentSection(href)) {
        link.setAttribute("aria-current", "page");
      }
      inner.appendChild(link);
    });

    const here = window.location.pathname.replace(/\\/g, "/");
    const group = document.createElement("div");
    group.className = "cat-group";
    const groupLink = document.createElement("a");
    groupLink.href = makeUrl("years.html");
    groupLink.textContent = "ഡിജിറ്റൽ ശേഖരം";
    const groupMenu = document.createElement("div");
    groupMenu.className = "cat-more-menu";
    let groupActive = /\/(2026|before2026|books|films|drama|literature|science|travel)\//.test(here) || /\/years\.html$/.test(here);
    archiveItems.forEach(([label, href]) => {
      const link = document.createElement("a");
      link.href = makeUrl(href);
      link.textContent = label;
      if (isCurrentSection(href)) {
        link.setAttribute("aria-current", "page");
        groupActive = true;
      }
      groupMenu.appendChild(link);
    });
    if (groupActive) {
      groupLink.setAttribute("aria-current", "page");
    }
    group.appendChild(groupLink);
    group.appendChild(groupMenu);
    inner.appendChild(group);

    const more = document.createElement("div");
    more.className = "cat-more";
    more.style.display = "none";
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "കൂടുതൽ ⋮";
    button.setAttribute("aria-haspopup", "true");
    const menu = document.createElement("div");
    menu.className = "cat-more-menu";
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      more.classList.toggle("open");
    });
    document.addEventListener("click", () => more.classList.remove("open"));
    more.appendChild(button);
    more.appendChild(menu);
    inner.appendChild(more);
    nav.appendChild(inner);

    document.body.insertBefore(nav, document.body.firstChild);
    document.body.insertBefore(top, document.body.firstChild);

    const links = Array.from(inner.querySelectorAll(":scope > a"));
    const fit = () => {
      links.forEach((link) => inner.insertBefore(link, group));
      more.style.display = "none";
      for (let i = links.length - 1; i >= 3 && inner.scrollWidth > inner.clientWidth + 1; i--) {
        more.style.display = "";
        menu.insertBefore(links[i], menu.firstChild);
      }
      button.removeAttribute("aria-current");
      if (menu.querySelector("[aria-current]")) {
        button.setAttribute("aria-current", "true");
      }
    };
    fit();
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(fit);
    }
    window.addEventListener("load", fit);
    let timer;
    window.addEventListener("resize", () => {
      clearTimeout(timer);
      timer = setTimeout(fit, 120);
    });
  }

  function addTicker() {
    const box = document.querySelector(".ticker-items");
    if (!box) {
      return;
    }
    const items = Array.from(box.querySelectorAll("a"));
    if (items.length < 2) {
      return;
    }
    box.classList.add("rotating");
    let i = 0;
    items[0].classList.add("on");
    setInterval(() => {
      items[i].classList.remove("on");
      i = (i + 1) % items.length;
      items[i].classList.add("on");
    }, 5000);
  }

  function addFooter() {
    const footer = document.querySelector("footer");
    if (!footer || footer.classList.contains("site-footer")) {
      return;
    }
    const copy = footer.textContent.replace(/\s+/g, " ").trim() || "© Sargavedi Readers Forum";
    const cols = footerColumns.map(([title, links]) =>
      "<div><h3>" + title + "</h3><ul>" +
      links.map(([label, href]) => "<li><a href=\"" + makeUrl(href) + "\">" + label + "</a></li>").join("") +
      "</ul></div>").join("");
    footer.classList.add("site-footer");
    footer.innerHTML =
      "<div class=\"foot-inner\"><div><h3>സർഗവേദി റീഡേഴ്സ് ഫോറം</h3>" +
      "<p>2006 മുതൽ ആലക്കോട് കേന്ദ്രീകരിച്ച് പ്രവർത്തിക്കുന്ന സാഹിത്യ-സാംസ്കാരിക കൂട്ടായ്മ. ഈ വെബ്സൈറ്റ് അതിന്റെ ഡിജിറ്റൽ ശേഖരമാണ്.</p>" +
      "<p>ആലക്കോട്, കണ്ണൂർ ജില്ല, കേരളം</p>" +
      "<p>ഫോൺ: <a href=\"tel:+919495358978\">9495358978</a> (എ.ആർ. പ്രസാദ്)<br>" +
      "<a href=\"mailto:sargavedireadersforumalakode@gmail.com\">sargavedireadersforumalakode@gmail.com</a></p>" +
      "<p><a href=\"https://www.facebook.com/share/g/1DUciCBZVe/\" target=\"_blank\" rel=\"noopener\">Facebook</a> · " +
      "<a href=\"https://www.youtube.com/@SargavediReadersForumAlakode\" target=\"_blank\" rel=\"noopener\">YouTube</a></p></div>" + cols + "</div>" +
      "<div class=\"foot-copy\">" + copy + "</div>";
  }

  async function addSidebar() {
    const page = document.querySelector(".page");
    if (!page || page.closest(".article-layout")) {
      return;
    }

    const layout = document.createElement("div");
    layout.className = "article-layout";
    page.before(layout);
    layout.appendChild(page);
    const aside = document.createElement("aside");
    aside.className = "article-side";
    layout.appendChild(aside);

    try {
      const response = await fetch(makeUrl("feed.json"));
      if (!response.ok) {
        throw new Error("no feed");
      }
      const feed = await response.json();
      const here = window.location.pathname;
      const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
      const events = feed.events.filter((e) => e.href && pathOf(e.href) !== here).slice(0, 5);
      const row = (e) =>
        "<a class=\"srow\" href=\"" + makeUrl(e.href) + "\">" +
        (e.thumb ? "<span class=\"sthumb\"><img src=\"" + makeUrl(e.thumb) + "\" alt=\"\" loading=\"lazy\"></span>" : "") +
        "<span class=\"fcat\">" + esc(e.cat) + "</span><span class=\"stitle\">" + esc(e.title) + "</span></a>";
      const bookRow = (b) =>
        "<a class=\"srow\" href=\"" + makeUrl(b.href) + "\"><span class=\"stitle\">" + esc(b.title) + "</span>" +
        "<span class=\"fmeta\">" + esc(b.author) + "</span></a>";
      aside.innerHTML =
        "<section class=\"box\"><h2>പുതിയ പരിപാടികൾ</h2>" + events.map(row).join("") + "</section>" +
        "<section class=\"box\"><h2>പുതിയ പുസ്തക നിരൂപണങ്ങൾ</h2>" + feed.books.slice(0, 5).map(bookRow).join("") + "</section>" +
        "<section class=\"box\"><h2>ഫോറത്തെ അറിയാൻ</h2>" +
        "<a class=\"srow\" href=\"" + makeUrl("about.html") + "\"><span class=\"stitle\">സർഗ്ഗവേദിയെക്കുറിച്ച്</span></a>" +
        "<a class=\"srow\" href=\"" + makeUrl("veettumuttam.html") + "\"><span class=\"stitle\">വീട്ടുമുറ്റ ചർച്ചകൾ</span></a>" +
        "<a class=\"srow\" href=\"" + makeUrl("awards.html") + "\"><span class=\"stitle\">പുരസ്കാരങ്ങൾ</span></a></section>";
    } catch (e) {
      layout.classList.add("no-side");
      aside.remove();
    }
  }

  // The top menu replaces the "← Back to ..." / "Home →" buttons; only
  // Previous Page / Next Page (and content buttons such as PDF links) stay.
  function removeBackButtons() {
    document.querySelectorAll(".navigation .nav-btn").forEach((btn) => {
      const text = btn.textContent.trim();
      if (/Previous Page|Next Page/.test(text)) {
        return;
      }
      if (/^←/.test(text) || /→$/.test(text)) {
        btn.remove();
      }
    });
    document.querySelectorAll(".navigation").forEach((box) => {
      if (!box.children.length) {
        box.remove();
      }
    });
  }

  function hideRepeatedTitle() {
    const h1 = document.querySelector(".hero h1");
    const h2 = document.querySelector(".page > h2");
    if (!h1 || !h2) {
      return;
    }
    const clean = (el) => el.textContent.replace(/[^\p{L}\p{N}]+/gu, "");
    const a = clean(h1);
    const b = clean(h2);
    if (a && b && (a === b || a.includes(b) || b.includes(a))) {
      h2.style.display = "none";
    }
  }

  function isSmallDisplay(img) {
    return /max-width:\s*\d+px/.test(img.getAttribute("style") || "");
  }

  function groupPhotos() {
    document.querySelectorAll(".page").forEach((page) => {
      let run = [];

      const flush = () => {
        if (run.length >= 2) {
          const grid = document.createElement("div");
          grid.className = "gallery-grid";
          run[0].before(grid);
          run.forEach((img) => grid.appendChild(img));
        }
        run = [];
      };

      Array.from(page.childNodes).forEach((node) => {
        if (node.nodeType === Node.ELEMENT_NODE && node.tagName === "IMG" && !isSmallDisplay(node)) {
          run.push(node);
        } else if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() === "") {
          return;
        } else {
          flush();
        }
      });

      flush();
    });
  }

  function addLightbox() {
    const photos = Array.from(document.querySelectorAll(".page img"));
    if (!photos.length) {
      return;
    }

    let index = 0;
    const box = document.createElement("div");
    box.className = "lightbox";
    box.setAttribute("role", "dialog");
    box.setAttribute("aria-modal", "true");
    box.innerHTML = "<button type=\"button\" class=\"lightbox-close\" aria-label=\"Close\">×</button>" +
      "<button type=\"button\" class=\"lightbox-prev\" aria-label=\"Previous photo\">‹</button>" +
      "<img alt=\"\">" +
      "<button type=\"button\" class=\"lightbox-next\" aria-label=\"Next photo\">›</button>" +
      "<div class=\"lightbox-count\"></div>";
    document.body.appendChild(box);

    const view = box.querySelector("img");
    const count = box.querySelector(".lightbox-count");

    function show(i) {
      index = (i + photos.length) % photos.length;
      view.src = photos[index].currentSrc || photos[index].src;
      view.alt = photos[index].alt || "";
      count.textContent = (index + 1) + " / " + photos.length;
    }

    function close() {
      box.classList.remove("open");
      document.body.style.overflow = "";
    }

    photos.forEach((img, i) => {
      img.classList.add("zoomable");
      img.addEventListener("click", () => {
        if (!isDesktop()) {
          return;
        }
        show(i);
        box.classList.add("open");
        document.body.style.overflow = "hidden";
      });
    });

    box.addEventListener("click", (event) => {
      if (event.target === box || event.target.classList.contains("lightbox-close")) {
        close();
      } else if (event.target.classList.contains("lightbox-prev")) {
        show(index - 1);
      } else if (event.target.classList.contains("lightbox-next")) {
        show(index + 1);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (!box.classList.contains("open")) {
        return;
      }
      if (event.key === "Escape") {
        close();
      } else if (event.key === "ArrowLeft") {
        show(index - 1);
      } else if (event.key === "ArrowRight") {
        show(index + 1);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    injectStyles();
    addBottomNav();

    if (isDesktop()) {
      injectDesktopStyles();
      addMasthead();
      addTicker();
      addFooter();
      removeBackButtons();
      hideRepeatedTitle();
      groupPhotos();
      addLightbox();
      addSidebar();
    }
  });
}());
