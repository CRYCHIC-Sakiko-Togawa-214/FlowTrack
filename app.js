/* FlowTrack result gallery: matched source / edited previews with no single-case player. */
(function () {
  "use strict";

  var cases = window.FLOWTRACK_CASES || [];
  var byId = new Map(cases.map(function (item) { return [item.id, item]; }));
  var $ = function (selector) { return document.querySelector(selector); };
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var categoryNames = { subject: "Subject replacement", color: "Color editing", material: "Material editing", creative: "Creative transformation", addition: "Object addition", removal: "Object removal" };
  var previews = new Map();
  var motionEnabled = !reducedMotion.matches;
  var galleryFilter = "all", galleryQuery = "", galleryLimit = 24;
  var selectedId = null;

  function updateURL(id) {
    var url = new URL(window.location.href);
    if (id) url.searchParams.set("case", id);
    else url.searchParams.delete("case");
    try { history.replaceState(null, "", url); } catch (_) {}
  }

  function selectCase(id, scrollToGallery, changeURL) {
    if (!byId.has(id)) return;
    selectedId = id;
    document.querySelectorAll(".case-card").forEach(function (card) {
      card.setAttribute("aria-pressed", String(card.dataset.case === id));
    });
    if (changeURL) updateURL(id);
    if (scrollToGallery) {
      var gallery = $("#gallery");
      if (gallery) gallery.scrollIntoView({ behavior: reducedMotion.matches ? "instant" : "smooth", block: "start" });
    }
  }

  function previewShouldPlay(entry) {
    return motionEnabled && entry.visible && !entry.element.hidden && !document.hidden;
  }

  function keepPreviewInSync(entry) {
    if (!previewShouldPlay(entry) || !entry.playingWanted) return;
    var master = entry.videos[0];
    var time = master.currentTime || 0;
    entry.videos.slice(1).forEach(function (video) {
      if (video.readyState >= 2 && !video.seeking && Math.abs(video.currentTime - time) > .08) {
        try { video.currentTime = time; } catch (_) {}
      }
      if (video.readyState >= 2 && video.paused) {
        video.play().catch(function () {});
      }
    });
  }

  async function startPreview(entry) {
    if (!previewShouldPlay(entry)) {
      entry.playingWanted = false;
      entry.videos.forEach(function (video) { video.pause(); });
      return;
    }
    if (!entry.loaded) {
      entry.loaded = true;
      entry.videos.forEach(function (video) { video.src = video.dataset.src; video.load(); });
    }
    if (entry.starting) return;
    if (!entry.videos.some(function (video) { return video.readyState >= 2; })) return;
    entry.starting = true;
    try {
      var master = entry.videos.find(function (video) { return video.readyState >= 2; }) || entry.videos[0];
      var time = master.ended ? 0 : master.currentTime;
      entry.videos.forEach(function (video) {
        if (video.readyState >= 1 && Math.abs(video.currentTime - time) > .08) video.currentTime = time;
        video.muted = true;
      });
      entry.playingWanted = true;
      // Start both videos in the same task. A source video can otherwise remain
      // paused after the edited result wins the autoplay race.
      await Promise.allSettled(entry.videos.map(function (video) { return video.play(); }));
      // Some Chromium builds resolve one autoplay promise while the paired
      // video remains paused. Explicitly resume every ready track and retry
      // once after the media pipeline has had a frame to settle.
      entry.videos.forEach(function (video) {
        if (video.readyState >= 2 && video.paused) video.play().catch(function () {});
      });
      keepPreviewInSync(entry);
      setTimeout(function () {
        if (!previewShouldPlay(entry) || !entry.playingWanted) return;
        entry.videos.forEach(function (video) {
          if (video.readyState >= 2 && video.paused) video.play().catch(function () {});
        });
        keepPreviewInSync(entry);
      }, 120);
    } finally {
      entry.starting = false;
    }
    if (!previewShouldPlay(entry)) {
      entry.playingWanted = false;
      entry.videos.forEach(function (video) { video.pause(); });
    }
  }

  var previewObserver = "IntersectionObserver" in window ? new IntersectionObserver(function (entries) {
    entries.forEach(function (observed) {
      var entry = previews.get(observed.target);
      if (!entry) return;
      entry.visible = observed.isIntersecting;
      if (entry.visible) startPreview(entry);
      else {
        entry.playingWanted = false;
        entry.videos.forEach(function (video) { video.pause(); });
      }
    });
  }, { threshold: .2 }) : null;

  function registerPreview(element, pair) {
    var entry = { element: element, videos: pair, visible: !previewObserver, loaded: false, starting: false, playingWanted: false };
    previews.set(element, entry);
    pair.forEach(function (video) {
      video.addEventListener("loadeddata", function () { startPreview(entry); });
      video.addEventListener("canplay", function () { startPreview(entry); });
      video.addEventListener("waiting", function () {
        if (previewShouldPlay(entry)) setTimeout(function () { startPreview(entry); }, 120);
      });
      video.addEventListener("pause", function () {
        if (entry.playingWanted && previewShouldPlay(entry)) setTimeout(function () { startPreview(entry); }, 80);
      });
      video.addEventListener("error", function () { element.classList.add("preview-error"); });
    });
    pair[0].addEventListener("timeupdate", function () {
      if (pair[0].paused) return;
      keepPreviewInSync(entry);
    });
    pair[0].addEventListener("ended", function () {
      entry.playingWanted = false;
      pair.forEach(function (video) { if (video.readyState >= 1) video.currentTime = 0; });
      startPreview(entry);
    });
    if (previewObserver) previewObserver.observe(element);
    else startPreview(entry);
  }

  function previewVideo(item, kind) {
    var video = document.createElement("video");
    video.muted = true;
    video.playsInline = true;
    video.preload = "none";
    video.poster = item.media[kind].poster;
    video.dataset.src = item.media[kind].src;
    video.setAttribute("aria-label", (kind === "source" ? "Original: " : "FlowTrack: ") + (kind === "source" ? item.before : item.after));
    video.setAttribute("disablepictureinpicture", "");
    return video;
  }

  function renderHero() {
    ["beach-zebra", "gym-panda", "plush-dog"].forEach(function (id) {
      var item = byId.get(id);
      if (!item) return;
      var card = document.createElement("button");
      card.type = "button";
      card.className = "hero-film";
      card.setAttribute("aria-label", "View " + item.before + " to " + item.after + " result");
      var output = previewVideo(item, "ours");
      var source = previewVideo(item, "source");
      output.className = "hero-output";
      var inset = document.createElement("div");
      inset.className = "hero-source";
      var sourceLabel = document.createElement("span");
      sourceLabel.textContent = "Original";
      inset.append(source, sourceLabel);
      var caption = document.createElement("div");
      caption.className = "hero-film-caption";
      var name = document.createElement("span");
      name.textContent = item.before + " → " + item.after;
      var label = document.createElement("span");
      label.textContent = "FlowTrack ↗";
      caption.append(name, label);
      card.append(output, inset, caption);
      card.addEventListener("click", function () { selectCase(id, true, true); });
      $("#hero-films").append(card);
      registerPreview(card, [output, source]);
    });
  }

  function renderGallery() {
    var grid = $("#case-grid");
    var groups = ["subject", "creative", "color", "material"].map(function (type) {
      return cases.filter(function (item) { return item.category === type; });
    });
    var ordered = [];
    while (groups.some(function (group) { return group.length; })) {
      groups.forEach(function (group) { if (group.length) ordered.push(group.shift()); });
    }
    ordered = ordered.concat(cases.filter(function (item) { return item.category === "addition" || item.category === "removal"; }));

    ordered.forEach(function (item) {
      var card = document.createElement("button");
      card.type = "button";
      card.className = "case-card";
      card.dataset.case = item.id;
      card.dataset.category = item.category;
      card.dataset.search = [item.before, item.after, item.instruction, item.targetPrompt].join(" ").toLowerCase();
      card.setAttribute("aria-pressed", "false");
      card.setAttribute("aria-label", "View " + item.before + " to " + item.after + " result");
      var frames = document.createElement("div");
      frames.className = "case-images";
      var pair = [];
      ["source", "ours"].forEach(function (kind) {
        var frame = document.createElement("div");
        frame.className = "case-image";
        var video = previewVideo(item, kind);
        pair.push(video);
        var label = document.createElement("span");
        label.textContent = kind === "source" ? "Original" : "FlowTrack";
        frame.append(video, label);
        frames.append(frame);
      });
      var body = document.createElement("div");
      body.className = "case-card-body";
      var meta = document.createElement("span");
      meta.className = "case-tag";
      meta.textContent = categoryNames[item.category] || item.category;
      var heading = document.createElement("h3");
      heading.textContent = item.before + " → " + item.after;
      var note = document.createElement("p");
      note.textContent = item.instruction;
      var action = document.createElement("span");
      action.className = "case-open";
      action.textContent = "View result ↗";
      body.append(meta, heading, note, action);
      card.append(frames, body);
      card.hidden = true;
      var galleryScrollY = null;
      card.addEventListener("mousedown", function (event) {
        galleryScrollY = window.scrollY;
        event.preventDefault();
      });
      card.addEventListener("click", function (event) {
        event.preventDefault();
        // Keep the reader anchored to the result wall when selecting a card.
        var keepScroll = galleryScrollY === null ? window.scrollY : galleryScrollY;
        selectCase(item.id, false, true);
        card.blur();
        window.scrollTo({ top: keepScroll, left: 0, behavior: "instant" });
        requestAnimationFrame(function () { window.scrollTo({ top: keepScroll, left: 0, behavior: "instant" }); });
        setTimeout(function () { window.scrollTo({ top: keepScroll, left: 0, behavior: "instant" }); }, 80);
      });
      grid.append(card);
      registerPreview(card, pair);
    });
    filterGallery();
  }

  function filterGallery() {
    var total = 0, shown = 0;
    document.querySelectorAll(".case-card").forEach(function (card) {
      var matches = (galleryFilter === "all" || card.dataset.category === galleryFilter) && (!galleryQuery || card.dataset.search.includes(galleryQuery));
      if (matches) total += 1;
      card.hidden = !matches || total > galleryLimit;
      if (!card.hidden) shown += 1;
      if (card.hidden) {
        var entry = previews.get(card);
        if (entry) entry.videos.forEach(function (video) { video.pause(); });
      }
    });
    $("#gallery-count").textContent = total ? "Showing selected examples" : "No matching examples. Try another search.";
    $("#load-more").hidden = shown >= total;
  }

  function updatePreviewMotion() {
    $("#gallery-motion").textContent = motionEnabled ? "Pause previews" : "Play previews";
    $("#gallery-motion").setAttribute("aria-pressed", String(motionEnabled));
    previews.forEach(function (entry) {
      if (previewShouldPlay(entry)) startPreview(entry);
      else {
        entry.playingWanted = false;
        entry.videos.forEach(function (video) { video.pause(); });
      }
    });
  }

  if (!cases.length) return;
  renderHero();
  renderGallery();
  // GitHub Pages or embedded browsers can occasionally miss the initial
  // IntersectionObserver callback after a cached navigation. Re-evaluate
  // visible cards once after layout so previews still begin reliably.
  setTimeout(function () {
    previews.forEach(function (entry) {
      var rect = entry.element.getBoundingClientRect();
      entry.visible = rect.bottom > 0 && rect.top < window.innerHeight;
      if (entry.visible) startPreview(entry);
    });
  }, 350);

  document.querySelectorAll(".filter-button").forEach(function (button) {
    button.addEventListener("click", function () {
      galleryFilter = button.dataset.filter;
      galleryLimit = 24;
      document.querySelectorAll(".filter-button").forEach(function (other) {
        var active = other === button;
        other.classList.toggle("active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      filterGallery();
    });
  });
  $("#case-search").addEventListener("input", function () {
    galleryQuery = this.value.trim().toLowerCase();
    galleryLimit = 24;
    filterGallery();
  });
  $("#load-more").addEventListener("click", function () { galleryLimit += 12; filterGallery(); });
  $("#gallery-motion").addEventListener("click", function () { motionEnabled = !motionEnabled; updatePreviewMotion(); });
  document.addEventListener("visibilitychange", updatePreviewMotion);
  reducedMotion.addEventListener("change", function (event) {
    motionEnabled = !event.matches;
    updatePreviewMotion();
  });

  var initialId = new URLSearchParams(location.search).get("case");
  if (byId.has(initialId)) selectCase(initialId, false, false);
  window.addEventListener("popstate", function () {
    var id = new URLSearchParams(location.search).get("case");
    if (byId.has(id)) selectCase(id, false, false);
  });
  updatePreviewMotion();
})();
