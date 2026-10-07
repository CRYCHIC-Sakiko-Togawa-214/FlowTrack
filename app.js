/* A small, dependency-free player for matched source / edit comparisons. */
(function () {
  "use strict";

  var cases = window.FLOWTRACK_CASES || [];
  var byId = new Map(cases.map(function (item) { return [item.id, item]; }));
  var $ = function (selector) { return document.querySelector(selector); };
  var videos = [$("#video-source"), $("#video-ours"), $("#video-baseline")];
  var master = videos[0];
  var stage = $("#comparison-stage");
  var viewer = $("#viewer");
  var timeline = $("#timeline");
  var playButton = $("#play-button");
  var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  var categoryNames = { subject: "Subject replacement", color: "Color editing", material: "Material editing", creative: "Creative transformation", addition: "Object addition", removal: "Object removal" };
  var state = {
    selected: null, mode: "grid", intentPlaying: !reducedMotion.matches,
    loading: true, duration: 0, speed: 1, scrubbing: false,
    visible: true, epoch: 0, playRequest: 0, controller: null, dragging: false
  };

  function availableVideos() { return state.selected && state.selected.media.baseline ? videos : videos.slice(0, 2); }
  function activeVideos() { return state.mode === "swipe" ? videos.slice(0, 2) : availableVideos(); }
  function status(message) { $("#player-status").textContent = message || ""; }
  function setPlayButton() {
    playButton.setAttribute("aria-label", state.intentPlaying ? "Pause all videos" : "Play all videos");
    playButton.querySelector("use").setAttribute("href", state.intentPlaying ? "#i-pause" : "#i-play");
  }
  function pauseActual() {
    state.playRequest += 1;
    videos.forEach(function (video) { video.pause(); });
  }
  function canPlay() {
    return !state.loading && state.intentPlaying && !state.scrubbing &&
      !document.hidden && state.visible;
  }
  function seekAll(time) {
    availableVideos().forEach(function (video) {
      if (video.readyState >= 1) video.currentTime = Math.max(0, Math.min(time, state.duration - 0.001));
    });
    updateTimeline();
  }
  async function playTogether() {
    if (!canPlay()) return;
    var request = ++state.playRequest;
    var epoch = state.epoch;
    var time = master.ended || master.currentTime >= state.duration - 0.01 ? 0 : master.currentTime;
    activeVideos().forEach(function (video) {
      if (Math.abs(video.currentTime - time) > 0.03) video.currentTime = time;
      video.playbackRate = state.speed;
    });
    var results = await Promise.allSettled(activeVideos().map(function (video) { return video.play(); }));
    if (request !== state.playRequest || epoch !== state.epoch) return;
    var blocked = results.some(function (result) {
      return result.status === "rejected" && result.reason.name !== "AbortError";
    });
    if (blocked) {
      state.intentPlaying = false;
      pauseActual();
      status("Press Play to start this comparison.");
      setPlayButton();
    }
  }
  function setLoading(value) {
    state.loading = value;
    $("#loading-overlay").hidden = !value;
    playButton.disabled = value;
    timeline.disabled = value;
    $("#restart-button").disabled = value;
  }
  function readyVideo(video, signal) {
    return new Promise(function (resolve, reject) {
      var timer;
      function cleanup() {
        clearTimeout(timer);
        video.removeEventListener("loadeddata", ready);
        video.removeEventListener("error", failed);
        signal.removeEventListener("abort", aborted);
      }
      function ready() { cleanup(); resolve(); }
      function failed() { cleanup(); reject(new Error("Video asset could not load: " + video.src)); }
      function aborted() { cleanup(); reject(new DOMException("Selection changed", "AbortError")); }
      if (signal.aborted) return aborted();
      if (video.readyState >= 2) return ready();
      video.addEventListener("loadeddata", ready);
      video.addEventListener("error", failed);
      signal.addEventListener("abort", aborted, { once: true });
      timer = setTimeout(failed, 20000);
    });
  }
  function updateTimeline() {
    var time = Math.min(master.currentTime || 0, state.duration || 0);
    if (!state.scrubbing) timeline.value = state.duration ? String(time / state.duration * 1000) : "0";
    $("#time-display").textContent = time.toFixed(1) + " / " + (state.duration || 0).toFixed(1) + "s";
    timeline.setAttribute("aria-valuetext", time.toFixed(1) + " of " + state.duration.toFixed(1) + " seconds");
  }
  function updateURL(id) {
    var url = new URL(window.location.href);
    url.searchParams.set("case", id);
    try { history.replaceState(null, "", url); } catch (_) { /* file previews may restrict history. */ }
  }
  async function selectCase(id, scroll, changeURL) {
    var item = byId.get(id);
    if (!item) return;
    if (state.controller) state.controller.abort();
    state.controller = new AbortController();
    var controller = state.controller;
    var epoch = ++state.epoch;
    pauseActual();
    state.selected = item;
    state.scrubbing = false;
    state.duration = item.duration;
    setLoading(true);
    status("");
    $("#case-number").textContent = String(cases.indexOf(item) + 1).padStart(2, "0");
    $("#case-category").textContent = categoryNames[item.category];
    var title = $("#case-title");
    title.replaceChildren(document.createTextNode(item.before + " "));
    var arrow = document.createElement("span");
    arrow.className = "edit-arrow";
    arrow.textContent = "→";
    title.append(arrow, document.createTextNode(" " + item.after));
    $("#edit-instruction").textContent = item.instruction;
    $("#source-prompt").textContent = item.sourcePrompt;
    $("#target-prompt").textContent = item.targetPrompt;
    stage.style.setProperty("--video-ratio", item.width + " / " + item.height);
    document.querySelectorAll(".case-card").forEach(function (card) {
      card.setAttribute("aria-pressed", String(card.dataset.case === id));
    });
    if (changeURL) updateURL(id);
    if (scroll) viewer.scrollIntoView({ behavior: reducedMotion.matches ? "instant" : "smooth", block: "start" });
    var kinds = ["source", "ours", "baseline"];
    stage.classList.toggle("no-baseline", !item.media.baseline);
    $(".baseline-panel").hidden = !item.media.baseline;
    if (!item.media.baseline) { videos[2].removeAttribute("src"); videos[2].removeAttribute("poster"); videos[2].load(); }
    availableVideos().forEach(function (video, index) {
      var media = item.media[kinds[index]];
      video.poster = media.poster;
      video.src = media.src;
      video.preload = "auto";
      video.playbackRate = state.speed;
      video.load();
    });
    updateTimeline();
    try {
      await Promise.all(availableVideos().map(function (video) { return readyVideo(video, controller.signal); }));
      if (epoch !== state.epoch) return;
      state.duration = Math.min.apply(null, availableVideos().map(function (video) { return video.duration; }));
      setLoading(false);
      seekAll(0);
      setPlayButton();
      await playTogether();
    } catch (error) {
      if (epoch !== state.epoch || error.name === "AbortError") return;
      setLoading(false);
      state.intentPlaying = false;
      setPlayButton();
      status("This experiment could not load. Try another example or reload the page.");
      console.error(error);
    }
  }

  // Preview videos load only on entering the viewport. Every preview is a matched pair.
  var previews = new Map();
  var motionEnabled = !reducedMotion.matches;
  var galleryFilter = "all", galleryQuery = "", galleryLimit = 24;
  function previewShouldPlay(entry) {
    return motionEnabled && entry.visible && !entry.element.hidden && !document.hidden;
  }
  async function startPreview(entry) {
    if (!previewShouldPlay(entry)) return;
    if (!entry.loaded) {
      entry.loaded = true;
      entry.videos.forEach(function (v) { v.src = v.dataset.src; v.load(); });
    }
    var ready = entry.videos.every(function (v) { return v.readyState >= 2; });
    if (!ready) return;
    var t = entry.videos[0].currentTime;
    entry.videos.slice(1).forEach(function (v) { if (Math.abs(v.currentTime - t) > .08) v.currentTime = t; });
    await Promise.allSettled(entry.videos.map(function (v) { return v.play(); }));
    if (!previewShouldPlay(entry)) entry.videos.forEach(function (v) { v.pause(); });
  }
  var previewObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (observed) {
      var entry = previews.get(observed.target);
      if (!entry) return;
      entry.visible = observed.isIntersecting;
      if (entry.visible) startPreview(entry);
      else entry.videos.forEach(function (v) { v.pause(); });
    });
  }, { threshold: .2 });
  function registerPreview(element, pair) {
    var entry = { element: element, videos: pair, visible: false, loaded: false };
    previews.set(element, entry);
    pair.forEach(function (v) {
      v.addEventListener("loadeddata", function () { startPreview(entry); });
      v.addEventListener("error", function () { element.classList.add("preview-error"); });
    });
    pair[0].addEventListener("timeupdate", function () {
      if (pair[0].paused) return;
      pair.slice(1).forEach(function (v) {
        if (v.readyState >= 2 && !v.seeking && Math.abs(v.currentTime - pair[0].currentTime) > .10) v.currentTime = pair[0].currentTime;
      });
    });
    pair[0].addEventListener("ended", function () {
      pair.forEach(function (v) { if (v.readyState >= 1) v.currentTime = 0; });
      startPreview(entry);
    });
    previewObserver.observe(element);
  }
  function previewVideo(item, kind) {
    var v = document.createElement("video");
    v.muted = true; v.playsInline = true; v.preload = "none";
    v.poster = item.media[kind].poster; v.dataset.src = item.media[kind].src;
    v.setAttribute("aria-label", (kind === "source" ? "Original: " + item.before : "FlowTrack: " + item.after));
    v.setAttribute("disablepictureinpicture", "");
    return v;
  }
  function renderHero() {
    ["beach-zebra", "gym-panda", "plush-dog"].forEach(function (id) {
      var item = byId.get(id), card = document.createElement("button");
      card.type = "button"; card.className = "hero-film";
      card.setAttribute("aria-label", "Compare " + item.before + " to " + item.after);
      var output = previewVideo(item, "ours"), source = previewVideo(item, "source");
      output.className = "hero-output";
      var inset = document.createElement("div"); inset.className = "hero-source";
      var sourceLabel = document.createElement("span"); sourceLabel.textContent = "Original";
      inset.append(source, sourceLabel);
      var caption = document.createElement("div"); caption.className = "hero-film-caption";
      var name = document.createElement("span"); name.textContent = item.before + " → " + item.after;
      var label = document.createElement("span"); label.textContent = "FlowTrack ↗";
      caption.append(name, label);
      card.append(output, inset, caption);
      card.addEventListener("click", function () { selectCase(id, true, true); });
      $("#hero-films").append(card);registerPreview(card, [output, source]);
    });
  }
  function renderGallery() {
    var grid = $("#case-grid");
    // Interleave edit types so the opening rows show the breadth of the method.
    var groups = ["subject", "creative", "color", "material"].map(function (type) { return cases.filter(function (c) { return c.category === type; }); });
    var ordered = [];
    while (groups.some(function (group) { return group.length; })) groups.forEach(function (group) { if (group.length) ordered.push(group.shift()); });
    ordered = ordered.concat(cases.filter(function (item) { return item.category === "addition" || item.category === "removal"; }));
    ordered.forEach(function (item) {
      var card = document.createElement("button");
      card.type = "button";card.className = "case-card";
      card.dataset.case = item.id;card.dataset.category = item.category;
      card.dataset.search = [item.before,item.after,item.instruction,item.targetPrompt].join(" ").toLowerCase();
      card.setAttribute("aria-pressed", "false");
      card.setAttribute("aria-label", "Compare " + item.before + " to " + item.after);
      var frames = document.createElement("div");frames.className = "case-images";
      var pair = [];
      ["source", "ours"].forEach(function (kind) {
        var frame = document.createElement("div");frame.className = "case-image";
        var v = previewVideo(item,kind);pair.push(v);
        var label = document.createElement("span");label.textContent = kind === "source" ? "Original" : "FlowTrack";
        frame.append(v,label);frames.append(frame);
      });
      var body = document.createElement("div");body.className = "case-card-body";
      var meta = document.createElement("span");meta.className = "case-tag";meta.textContent = categoryNames[item.category];
      var heading = document.createElement("h3");heading.textContent = item.before + " → " + item.after;
      var note = document.createElement("p");note.textContent = item.instruction;
      var action = document.createElement("span");action.className = "case-open";action.textContent = "Compare ↗";
      body.append(meta,heading,note,action);card.append(frames,body);
      card.addEventListener("click", function () { selectCase(item.id,true,true); });
      card.hidden = true;grid.append(card);registerPreview(card,pair);
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
      if (card.hidden) previews.get(card).videos.forEach(function (v) { v.pause(); });
    });
    $("#gallery-count").textContent = total ? "Showing " + shown + " of " + total + " examples" : "No matching examples. Try another search.";
    $("#load-more").hidden = shown >= total;
  }
  document.querySelectorAll(".filter-button").forEach(function (button) {
    button.addEventListener("click", function () {
      galleryFilter = button.dataset.filter;galleryLimit = 24;
      document.querySelectorAll(".filter-button").forEach(function (other) {
        var active = other === button;other.classList.toggle("active",active);other.setAttribute("aria-pressed",String(active));
      });
      filterGallery();
    });
  });
  $("#case-search").addEventListener("input", function () { galleryQuery = this.value.trim().toLowerCase();galleryLimit = 24;filterGallery(); });
  $("#load-more").addEventListener("click", function () { galleryLimit += 12;filterGallery(); });
  function updatePreviewMotion() {
    $("#gallery-motion").textContent = motionEnabled ? "Pause previews" : "Play previews";
    $("#gallery-motion").setAttribute("aria-pressed",String(motionEnabled));
    previews.forEach(function (entry) {
      if (previewShouldPlay(entry)) startPreview(entry);
      else entry.videos.forEach(function (v) { v.pause(); });
    });
  }
  $("#gallery-motion").addEventListener("click", function () { motionEnabled = !motionEnabled;updatePreviewMotion(); });
  document.addEventListener("visibilitychange", updatePreviewMotion);
  reducedMotion.addEventListener("change", function (event) { if (event.matches) { motionEnabled = false;updatePreviewMotion(); } });

  document.querySelectorAll(".mode-button").forEach(function (button) {
    button.addEventListener("click", function () {
      state.mode = button.dataset.mode;
      stage.dataset.mode = state.mode;
      $("#split-controls").hidden = state.mode !== "swipe";
      document.querySelectorAll(".mode-button").forEach(function (other) {
        var active = other === button;
        other.classList.toggle("active", active);
        other.setAttribute("aria-pressed", String(active));
      });
      if (state.mode === "swipe") videos[2].pause();
      playTogether();
    });
  });
  playButton.addEventListener("click", function () {
    state.intentPlaying = !state.intentPlaying;
    status("");
    setPlayButton();
    if (state.intentPlaying) playTogether(); else pauseActual();
  });
  $("#restart-button").addEventListener("click", function () {
    pauseActual();
    seekAll(0);
    playTogether();
  });
  timeline.addEventListener("input", function () {
    state.scrubbing = true;
    pauseActual();
    seekAll(Number(timeline.value) / 1000 * state.duration);
  });
  timeline.addEventListener("change", function () {
    state.scrubbing = false;
    playTogether();
  });
  $("#speed-button").addEventListener("click", function () {
    state.speed = state.speed === 1 ? 0.5 : 1;
    videos.forEach(function (video) { video.playbackRate = state.speed; });
    this.textContent = state.speed === 1 ? "1×" : "0.5×";
    this.setAttribute("aria-label", state.speed === 1 ? "Switch to half speed" : "Switch to normal speed");
  });
  $("#fullscreen-button").addEventListener("click", async function () {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else if (viewer.requestFullscreen) await viewer.requestFullscreen();
      else status("Fullscreen is unavailable here. You can use your browser's fullscreen view.");
    } catch (_) { status("Fullscreen is unavailable here. You can use your browser's fullscreen view."); }
  });
  master.addEventListener("ended", function () {
    if (!state.loading && state.intentPlaying && !state.scrubbing) {
      seekAll(0);
      playTogether();
    }
  });
  master.addEventListener("waiting", function () {
    if (canPlay()) videos.slice(1).forEach(function (video) { video.pause(); });
  });
  master.addEventListener("playing", function () {
    if (canPlay()) activeVideos().slice(1).forEach(function (video) {
      video.play().catch(function () { /* The group player reports autoplay blocking. */ });
    });
  });
  document.addEventListener("visibilitychange", function () {
    if (document.hidden) pauseActual(); else playTogether();
  });
  reducedMotion.addEventListener("change", function (event) {
    if (event.matches) {
      state.intentPlaying = false;
      pauseActual();
      setPlayButton();
    }
  });
  if ("IntersectionObserver" in window) {
    var visibilityObserver = new IntersectionObserver(function (entries) {
      state.visible = entries[0].isIntersecting;
      if (state.visible) playTogether(); else pauseActual();
    }, { threshold: 0.05 });
    visibilityObserver.observe(viewer);
  }

  function setSplit(value) {
    var split = Math.max(2, Math.min(98, value));
    stage.style.setProperty("--split", split + "%");
    $("#split-range").value = String(split);
  }
  $("#split-range").addEventListener("input", function () { setSplit(Number(this.value)); });
  var divider = $("#swipe-divider");
  function dragSplit(event) {
    var box = stage.getBoundingClientRect();
    setSplit((event.clientX - box.left) / box.width * 100);
  }
  divider.addEventListener("pointerdown", function (event) {
    state.dragging = true;
    divider.setPointerCapture(event.pointerId);
    dragSplit(event);
  });
  divider.addEventListener("pointermove", function (event) {
    if (state.dragging) dragSplit(event);
  });
  divider.addEventListener("pointerup", function () { state.dragging = false; });
  divider.addEventListener("pointercancel", function () { state.dragging = false; });

  $("#copy-case").addEventListener("click", async function () {
    if (!state.selected) return;
    var url = new URL(window.location.href);
    url.searchParams.set("case", state.selected.id);
    url.hash = "showcase";
    try {
      if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(url.href);
      else {
        var input = document.createElement("textarea");
        input.value = url.href;
        input.style.position = "fixed";
        input.style.opacity = "0";
        document.body.append(input);
        input.select();
        if (!document.execCommand("copy")) throw new Error("Copy not supported");
        input.remove();
      }
      var label = this.querySelector("span");
      label.textContent = "Link copied";
      this.setAttribute("aria-label", "Example link copied");
      setTimeout(function () {
        label.textContent = "Copy example link";
        $("#copy-case").setAttribute("aria-label", "Copy example link");
      }, 2000);
      status("Example link copied.");
      setTimeout(function () { if ($("#player-status").textContent === "Example link copied.") status(""); }, 2000);
    } catch (_) { status("To share this example, copy the current page address from your browser."); }
  });
  window.addEventListener("popstate", function () {
    var id = new URLSearchParams(location.search).get("case");
    selectCase(byId.has(id) ? id : cases[0].id, false, false);
  });

  function tick() {
    if (!state.loading) {
      updateTimeline();
      if (!master.paused && !master.seeking && !state.scrubbing) {
        activeVideos().slice(1).forEach(function (video) {
          if (video.readyState >= 2 && !video.seeking &&
              Math.abs(video.currentTime - master.currentTime) > 0.075) {
            video.currentTime = master.currentTime;
          }
        });
      }
    }
    requestAnimationFrame(tick);
  }

  if (!cases.length) {
    $("#loading-overlay").hidden = true;
    status("The example collection is unavailable. Please reload the page.");
    return;
  }
  renderHero();
  renderGallery();
  updatePreviewMotion();
  var initialId = new URLSearchParams(location.search).get("case");
  selectCase(byId.has(initialId) ? initialId : cases[0].id, false, false);
  setPlayButton();
  requestAnimationFrame(tick);
})();
