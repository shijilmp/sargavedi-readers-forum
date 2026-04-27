const path = window.location.pathname;
const match = path.match(/page(\d+)\.html/);

if(match){
let page = parseInt(match[1]);

const prevBtn = document.getElementById("prevBtn");
const nextBtn = document.getElementById("nextBtn");
const pageLabel = document.getElementById("pageNumber");

if(pageLabel){
pageLabel.innerText = "Page " + page;
}

const prevPage = "page" + (page - 1) + ".html";
const nextPage = "page" + (page + 1) + ".html";

if(page === 1){
prevBtn.style.display = "none";
}else{
prevBtn.onclick = () => window.location.href = prevPage;
}

nextBtn.onclick = () => window.location.href = nextPage;
}
