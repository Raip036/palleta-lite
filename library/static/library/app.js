(function () {
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------- Top bar turns solid after scrolling ----------
  var topbar = document.getElementById("topbar");
  function onScroll() { topbar.classList.toggle("scrolled", window.scrollY > 20); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ---------- Toasts fade out on their own ----------
  document.querySelectorAll(".message").forEach(function (m) {
    setTimeout(function () {
      m.classList.add("hide");
      setTimeout(function () { m.remove(); }, 350);
    }, 4000);
  });

  // ---------- Hero video ----------
  var hero = document.querySelector(".hero-video");
  if (hero && reduceMotion) hero.pause();

  // ---------- Lightbox player ----------
  var dialog = document.getElementById("player");
  if (dialog) {
    var video = document.getElementById("player-video");
    var title = document.getElementById("player-title");

    function openPlayer(src, name) {
      title.textContent = name;
      video.src = src;
      if (hero) hero.pause();
      dialog.showModal();
      video.play().catch(function () {});
    }

    dialog.addEventListener("close", function () {   // also fires on Esc
      video.pause();
      video.removeAttribute("src");
      video.load();
      if (hero && !reduceMotion) hero.play().catch(function () {});
    });

    document.querySelectorAll("[data-play]").forEach(function (el) {
      el.addEventListener("click", function () {
        openPlayer(el.dataset.src, el.dataset.title);
      });
    });
    document.getElementById("player-close").addEventListener("click", function () { dialog.close(); });
    dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });

    // Hover preview, after a short delay so quick passes don't start playback
    if (window.matchMedia("(hover: hover)").matches && !reduceMotion) {
      document.querySelectorAll(".thumb").forEach(function (thumb) {
        var v = thumb.querySelector("video");
        var timer;
        thumb.addEventListener("mouseenter", function () {
          timer = setTimeout(function () { v.play().catch(function () {}); }, 350);
        });
        thumb.addEventListener("mouseleave", function () {
          clearTimeout(timer);
          v.pause();
          v.currentTime = 0.5;
        });
      });
    }
  }

  // ---------- Delete confirmation ----------
  var confirmDialog = document.getElementById("delete-dialog");
  if (confirmDialog) {
    var delForm = document.getElementById("delete-form");
    var delName = document.getElementById("delete-title");
    var delBtn = document.getElementById("delete-confirm");

    document.querySelectorAll("[data-delete]").forEach(function (el) {
      el.addEventListener("click", function () {
        delForm.action = el.dataset.deleteUrl;
        delName.textContent = el.dataset.title;
        confirmDialog.showModal();
      });
    });
    document.getElementById("delete-cancel").addEventListener("click", function () { confirmDialog.close(); });
    confirmDialog.addEventListener("click", function (e) { if (e.target === confirmDialog) confirmDialog.close(); });
    delForm.addEventListener("submit", function () {
      delBtn.disabled = true;
      delBtn.classList.add("loading");
      delBtn.textContent = "Deleting…";
    });
  }

  // ---------- Upload page ----------
  var input = document.querySelector("#dropzone input[type=file]");
  if (input) {
    var zone = document.getElementById("dropzone");
    var list = document.getElementById("file-list");
    var btn = document.getElementById("submit-btn");
    var form = document.getElementById("upload-form");

    function size(bytes) {
      if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
      return Math.max(1, Math.round(bytes / 1024)) + " KB";
    }

    function render() {
      list.innerHTML = "";
      Array.prototype.forEach.call(input.files, function (f) {
        var li = document.createElement("li");
        var name = document.createElement("span");
        name.textContent = f.name;
        var meta = document.createElement("span");
        meta.className = "muted";
        meta.textContent = size(f.size);
        li.appendChild(name);
        li.appendChild(meta);
        list.appendChild(li);
      });
      var n = input.files.length;
      btn.disabled = n === 0;
      btn.textContent = n > 1 ? "Upload " + n + " videos" : "Upload";
    }

    input.addEventListener("change", render);
    ["dragenter", "dragover"].forEach(function (evt) {
      zone.addEventListener(evt, function () { zone.classList.add("over"); });
    });
    ["dragleave", "drop"].forEach(function (evt) {
      zone.addEventListener(evt, function () { zone.classList.remove("over"); });
    });

    form.addEventListener("submit", function () {
      btn.disabled = true;
      btn.classList.add("loading");
      btn.textContent = "Uploading…";
    });
  }
})();
