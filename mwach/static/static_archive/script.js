/**
 * @param {String} HTML representing a single element
 * @return {Element}
 */
function htmlToElement(html) {
    var template = document.createElement('template');
    html = html.trim(); // Never return a text node of whitespace as the result
    template.innerHTML = html;
    return template.content.firstChild;
}

function init() {
  var tab_sections = document.querySelectorAll("section.tab");
  var menu_bar = document.querySelector("#menu-bar");

  // Set up tabs
  tab_sections.forEach( function(tab) {
    let li = htmlToElement(`<li id="${tab.id}">${tab.id.replace("-"," ")}</li>`);
    li.addEventListener("click", menu_click);
    menu_bar.appendChild(li);
  });

  // Set up translation toggle
  document.querySelector("input[name=toggle-translate]").addEventListener("click", toggle_translate);

  var anchor = location.hash || "#messages";
  if (anchor.startsWith("#")) {
    document.querySelector(anchor).click();
  }
}

function menu_click() {
  var cur = document.querySelector('section.visible');
  var nxt = document.querySelector(`section#${this.id}`);
  cur.classList.remove("visible");
  nxt.classList.add("visible");
  location.hash = `#${this.id}`
  var toggle = document.querySelector("#translate-sms");
  console.log(this.id, toggle);
  if (this.id == "messages") {
    toggle.classList.replace('d-none','d-block');
  } else {
    toggle.classList.replace('d-block','d-none');
  }
}

function toggle_translate() {
  // var toggle = document.querySelector("input[name=toggle-translate");
  var filter = this.checked ? "original" : "translation";
  var messages = document.querySelectorAll("div.content");
  messages.forEach( function(msg) {
      if (msg.classList.contains(filter)) {
        msg.classList.add("visible");
      } else {
        msg.classList.remove("visible");
      }
  });

}


window.addEventListener("load", init);
