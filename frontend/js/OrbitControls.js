// 手写 OrbitControls - 简单可靠版本
(function() {
  function init() {
    const cam = window.__camera;
    const renderer = window.__renderer;
    if (!cam || !renderer) { console.warn('[OrbitCtrl] waiting...'); setTimeout(init, 50); return; }
    const dom = renderer.domElement;
    if (!dom) { console.warn('[OrbitCtrl] no dom'); setTimeout(init, 50); return; }
    console.log('[OrbitCtrl] init on', dom.tagName);
    const ROT = 0.005, ZOOM = 0.1;
    const target = new THREE.Vector3(0, 0, 0);
    let radius = 280, theta = 0, phi = Math.PI / 2;
    let isDragging = false, prevX = 0, prevY = 0;
    function updateCamera() {
      cam.position.x = target.x + radius * Math.sin(phi) * Math.cos(theta);
      cam.position.y = target.y + radius * Math.cos(phi);
      cam.position.z = target.z + radius * Math.sin(phi) * Math.sin(theta);
      cam.lookAt(target);
    }
    updateCamera();
    dom.addEventListener("mousedown", e => { isDragging = true; prevX = e.clientX; prevY = e.clientY; });
    window.addEventListener("mouseup", () => { isDragging = false; });
    window.addEventListener("mousemove", e => {
      if (!isDragging) return;
      theta += (e.clientX - prevX) * ROT;
      phi = Math.max(0.2, Math.min(Math.PI - 0.2, phi - (e.clientY - prevY) * ROT));
      prevX = e.clientX; prevY = e.clientY;
      updateCamera();
    });
    dom.addEventListener("wheel", e => {
      e.preventDefault();
      radius = Math.max(150, Math.min(500, radius * (1 + Math.sign(e.deltaY) * ZOOM)));
      updateCamera();
    }, { passive: false });
    // 触摸
    let tp = null;
    dom.addEventListener("touchstart", e => { if (e.touches.length===1) tp = [e.touches[0].clientX, e.touches[0].clientY]; });
    dom.addEventListener("touchmove", e => {
      if (tp && e.touches.length===1) {
        theta += (e.touches[0].clientX - tp[0]) * ROT;
        phi = Math.max(0.2, Math.min(Math.PI - 0.2, phi - (e.touches[0].clientY - tp[1]) * ROT));
        tp = [e.touches[0].clientX, e.touches[0].clientY];
        updateCamera();
      }
      e.preventDefault();
    }, { passive: false });
    // 合并到现有的 controls 对象 (主代码会读它)
    if (window.__OrbitControls) {
      window.__OrbitControls.update = () => {};
      window.__OrbitControls.updateCamera = updateCamera;
    } else {
      window.__OrbitControls = { update: () => {}, updateCamera };
    }
    console.log('[OrbitCtrl] ready');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
