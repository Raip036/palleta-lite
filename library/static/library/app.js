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

    var progress = document.getElementById("progress");
    var fill = document.getElementById("progress-fill");
    var bar = document.getElementById("progress-bar");
    var pctEl = document.getElementById("progress-pct");
    var label = document.getElementById("progress-label");
    var detail = document.getElementById("progress-detail");
    var errorEl = document.getElementById("upload-error");
    var cancelLink = document.getElementById("cancel-link");
    var tagsInput = form.querySelector("input[type=text]");
    var xhr = null;

    function showError(text) {
      errorEl.textContent = text;
      errorEl.hidden = false;
    }

    function reset() {
      xhr = null;
      form.classList.remove("busy");
      progress.hidden = true;
      progress.classList.remove("processing");
      input.disabled = false;
      tagsInput.disabled = false;
      btn.classList.remove("loading");
      cancelLink.textContent = "Cancel";
      Array.prototype.forEach.call(list.children, function (li) { li.classList.remove("done"); });
      render();
    }

    function setProgress(pct) {
      fill.style.transform = "scaleX(" + pct / 100 + ")";
      pctEl.textContent = pct + "%";
      bar.setAttribute("aria-valuenow", pct);
    }

    // Cancel aborts an upload in progress; otherwise it's a normal link back
    cancelLink.addEventListener("click", function (e) {
      if (xhr) { e.preventDefault(); xhr.abort(); }
    });

    window.addEventListener("beforeunload", function (e) {
      if (xhr) { e.preventDefault(); e.returnValue = ""; }
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!input.files.length || xhr) return;

      var data = new FormData(form);   // build before disabling inputs
      var files = Array.prototype.slice.call(input.files);
      var total = files.reduce(function (sum, f) { return sum + f.size; }, 0);
      var ends = [], running = 0;
      files.forEach(function (f) { running += f.size; ends.push(running); });

      errorEl.hidden = true;
      form.classList.add("busy");
      input.disabled = true;
      tagsInput.disabled = true;
      btn.disabled = true;
      btn.classList.add("loading");
      btn.textContent = "Uploading…";
      cancelLink.textContent = "Cancel upload";
      label.textContent = files.length > 1 ? "Uploading " + files.length + " videos" : "Uploading video";
      setProgress(0);
      detail.textContent = "0 MB of " + size(total);
      progress.hidden = false;

      xhr = new XMLHttpRequest();
      xhr.open("POST", window.location.href);
      xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

      xhr.upload.addEventListener("progress", function (ev) {
        if (!ev.lengthComputable) return;
        setProgress(Math.min(100, Math.round(ev.loaded / ev.total * 100)));
        var sent = Math.min(total, ev.loaded);
        detail.textContent = size(sent) + " of " + size(total);
        // Tick off files whose bytes have all been sent (multipart sends them in order)
        ends.forEach(function (end, i) {
          if (sent >= end && list.children[i]) list.children[i].classList.add("done");
        });
      });

      xhr.upload.addEventListener("load", function () {
        setProgress(100);
        progress.classList.add("processing");
        label.textContent = "Finishing up…";
        detail.textContent = "Saving to your library";
        Array.prototype.forEach.call(list.children, function (li) { li.classList.add("done"); });
      });

      xhr.addEventListener("load", function () {
        var status = this.status;
        var body = {};
        try { body = JSON.parse(xhr.responseText); } catch (err) {}
        if (xhr.status === 200 && body.redirect) {
          xhr = null;   // allow navigation without the leave-page warning
          window.location.href = body.redirect;
          return;
        }
        reset();
        if (body.errors) {
          var first = Object.keys(body.errors)[0];
          showError(body.errors[first][0]);
        } else {
          showError("Upload failed (error " + status + "). Try again.");
        }
      });

      xhr.addEventListener("error", function () {
        reset();
        showError("Upload failed: check your connection and try again.");
      });

      xhr.addEventListener("abort", function () {
        reset();
        showError("Upload cancelled. Your files are still selected.");
      });

      xhr.send(data);
    });
  }
})();
