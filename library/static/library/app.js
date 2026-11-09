(function () {
  // ---------- Gallery: lightbox player + hover preview ----------
  var dialog = document.getElementById("player");
  if (dialog) {
    var video = document.getElementById("player-video");
    var title = document.getElementById("player-title");

    function openPlayer(src, name) {
      title.textContent = name;
      video.src = src;
      dialog.showModal();
      video.play().catch(function () {});
    }

    function stopPlayer() {
      video.pause();
      video.removeAttribute("src");
      video.load();
    }

    document.querySelectorAll("[data-play]").forEach(function (el) {
      el.addEventListener("click", function () {
        openPlayer(el.dataset.src, el.dataset.title);
      });
    });

    document.getElementById("player-close").addEventListener("click", function () {
      dialog.close();
    });
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog) dialog.close();   // click on backdrop
    });
    dialog.addEventListener("close", stopPlayer);  // also fires on Esc

    if (window.matchMedia("(hover: hover)").matches) {
      document.querySelectorAll(".thumb").forEach(function (thumb) {
        var v = thumb.querySelector("video");
        thumb.addEventListener("mouseenter", function () { v.play().catch(function () {}); });
        thumb.addEventListener("mouseleave", function () { v.pause(); v.currentTime = 0.5; });
      });
    }
  }

  // ---------- Upload page: file list + submit state ----------
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
        meta.className = "muted small";
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
