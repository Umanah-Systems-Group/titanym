/* Titanym 3D wafer: loads the Blender model (images/titanym-wafer.glb) into the hero and the
   technology cutaway. Drag to spin it a full 360°; scrolling the cutaway pulls the layers apart. */
import * as THREE from 'three';
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
import { RoomEnvironment } from './vendor/jsm/environments/RoomEnvironment.js';

const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const LAYERS = { rf: 'RF', sapphire: 'Sapphire', sige: 'SiGe' };
const BASE = { RF: 0.085, Sapphire: 0, SiGe: -0.085 };

function supportsGL() {
  try {
    const c = document.createElement('canvas');
    return !!(c.getContext('webgl2') || c.getContext('webgl'));
  } catch (e) { return false; }
}

function glowTexture() {
  const c = document.createElement('canvas');
  c.width = c.height = 256;
  const g = c.getContext('2d');
  const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  grad.addColorStop(0, 'rgba(90,150,255,0.45)');
  grad.addColorStop(0.5, 'rgba(60,110,230,0.12)');
  grad.addColorStop(1, 'rgba(40,80,200,0)');
  g.fillStyle = grad;
  g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

class WaferView {
  constructor(el, gltfScene, mode) {
    this.el = el;
    this.mode = mode;
    this.visible = true;
    this.explode = mode === 'hero' ? 0.25 : 0;
    this.layer = 'all';

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    el.appendChild(renderer.domElement);
    this.renderer = renderer;

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environmentIntensity = 0.85;
    const key = new THREE.DirectionalLight(0xffd9a0, 3.2);
    key.position.set(2.5, 4, 2.5);
    const rim = new THREE.DirectionalLight(0x6fa2ff, 2.2);
    rim.position.set(-3, 1.2, -2.5);
    const fill = new THREE.DirectionalLight(0x5b86c9, 0.8);
    fill.position.set(0, -3, 3);
    scene.add(key, rim, fill, new THREE.AmbientLight(0x1e3a5f, 0.6));
    this.scene = scene;

    this.camera = new THREE.PerspectiveCamera(28, 1, 0.1, 50);

    // The spin rig: yaw (drag left/right, full 360°) inside a tilt (drag up/down, limited).
    this.tilt = new THREE.Group();
    this.spin = new THREE.Group();
    this.tilt.add(this.spin);
    scene.add(this.tilt);

    const model = gltfScene.clone(true);
    // Each view gets its own materials so the cutaway can dim layers independently.
    model.traverse((o) => {
      if (o.isMesh) {
        o.material = o.material.clone();
        o.material.userData.baseOpacity = o.material.opacity;
        o.material.userData.baseEmissive = o.material.emissiveIntensity;
        if (o.material.transparent) o.material.depthWrite = false;
        o.renderOrder = o.material.transparent ? 2 : 1;
      }
    });
    this.spin.add(model);
    this.nodes = {
      RF: model.getObjectByName('RF'),
      Sapphire: model.getObjectByName('Sapphire'),
      SiGe: model.getObjectByName('SiGe'),
      Vias: model.getObjectByName('Vias'),
    };
    this.viaMats = [];
    this.nodes.Vias.traverse((o) => { if (o.isMesh) this.viaMats.push(o.material); });
    this.dim = { RF: 1, Sapphire: 1, SiGe: 1 };

    const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
    glow.scale.set(2.6, 2.6, 1);
    glow.renderOrder = 0;
    this.spin.add(glow);
    this.glow = glow;

    // Drag to rotate. touch-action: pan-y in CSS keeps vertical page scrolling on phones.
    this.yaw = -0.5; this.pitch = 0; this.vel = 0; this.dragging = false; this.idle = 0;
    this.targetPitch = 0;
    let lastX = 0, lastY = 0;
    const cv = renderer.domElement;
    cv.addEventListener('pointerdown', (e) => {
      this.dragging = true; lastX = e.clientX; lastY = e.clientY;
      cv.setPointerCapture(e.pointerId); el.classList.add('is-grabbing'); el.classList.add('was-dragged');
    });
    cv.addEventListener('pointermove', (e) => {
      if (!this.dragging) return;
      const dx = e.clientX - lastX, dy = e.clientY - lastY;
      lastX = e.clientX; lastY = e.clientY;
      this.vel = dx * 0.0085;
      this.yaw += this.vel;
      this.targetPitch = clamp(this.targetPitch + dy * 0.005, -0.45, 0.55);
    });
    const end = () => { this.dragging = false; this.idle = 0; el.classList.remove('is-grabbing'); };
    cv.addEventListener('pointerup', end);
    cv.addEventListener('pointercancel', end);

    this.resize();
  }

  resize() {
    const w = this.el.clientWidth, h = this.el.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    // Fit the wafer (radius 1) plus the exploded stack in view, from a raised angle.
    const fitH = this.mode === 'hero' ? 2.35 : 3.1;
    const fitW = this.mode === 'hero' ? 2.3 : (w > 520 ? 3.0 : 2.4);
    const fov = THREE.MathUtils.degToRad(this.camera.fov);
    const distH = fitH / 2 / Math.tan(fov / 2);
    const distW = fitW / 2 / Math.tan(fov / 2) / this.camera.aspect;
    const dist = Math.max(distH, distW) * 1.04;
    const elev = THREE.MathUtils.degToRad(this.mode === 'hero' ? 32 : 26);
    this.camera.position.set(0, Math.sin(elev) * dist, Math.cos(elev) * dist);
    this.camera.lookAt(0, 0, 0);
    // In the wide cutaway, sit the wafer left of centre so the layer labels fit on the right.
    if (this.mode === 'cut' && w > 520) this.camera.setViewOffset(w, h, w * 0.12, 0, w, h);
    else this.camera.clearViewOffset();
    this.camera.updateProjectionMatrix();
  }

  update(dt, t) {
    if (!this.dragging) {
      this.idle += dt;
      this.vel *= Math.pow(0.04, dt);
      const auto = reduced ? 0 : (this.mode === 'hero' ? 0.28 : 0.12);
      const blend = clamp((this.idle - 1.2) / 1.5, 0, 1);
      this.yaw += this.vel + auto * dt * blend;
      if (this.idle > 2.5) this.targetPitch *= Math.pow(0.5, dt);
    }
    this.pitch += (this.targetPitch - this.pitch) * Math.min(1, dt * 8);
    this.spin.rotation.y = this.yaw;
    this.tilt.rotation.x = this.pitch;

    let ex = this.explode;
    if (this.mode === 'hero' && !reduced) ex = 0.2 + 0.12 * (0.5 + 0.5 * Math.sin(t * 0.9));
    const gap = ex;
    this.nodes.RF.position.y = BASE.RF + gap;
    this.nodes.SiGe.position.y = BASE.SiGe - gap;
    this.nodes.Vias.scale.y = 0.17 + gap * 2;

    const want = this.layer;
    for (const key of ['RF', 'Sapphire', 'SiGe']) {
      const on = want === 'all' || want === 'int' || LAYERS[want] === key;
      this.dim[key] += ((on ? 1 : 0.16) - this.dim[key]) * Math.min(1, dt * 6);
      this.nodes[key].traverse((o) => {
        if (!o.isMesh) return;
        const m = o.material, d = this.dim[key];
        const base = m.userData.baseOpacity;
        const target = base * d;
        if (target < 0.999 && !m.transparent) { m.transparent = true; m.depthWrite = false; m.needsUpdate = true; }
        m.opacity = target;
        m.emissiveIntensity = m.userData.baseEmissive * (0.35 + 0.65 * d);
      });
    }
    const viaOn = this.mode === 'hero' || want === 'int' || want === 'all';
    const pulse = want === 'int' ? 1.6 + 1.4 * Math.sin(t * 6) : 1;
    this.viaMats.forEach((m) => { m.emissiveIntensity = m.userData.baseEmissive * (viaOn ? pulse : 0.2); m.transparent = true; m.opacity = viaOn ? 1 : 0.25; });
    this.glow.material.opacity = 0.6 + 0.4 * this.dim.Sapphire;

    this.renderer.render(this.scene, this.camera);
  }

  // Screen position (relative to the view) of a layer's right-hand edge, for the cutaway labels.
  edge(name) {
    const node = this.nodes[name];
    const p = new THREE.Vector3();
    node.getWorldPosition(p);
    const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this.camera.quaternion).multiplyScalar(1.0);
    p.add(right).project(this.camera);
    return { x: (p.x + 1) / 2 * this.el.clientWidth, y: (1 - p.y) / 2 * this.el.clientHeight };
  }
}

async function start() {
  const heroEl = document.getElementById('hero-gl');
  const cutEl = document.getElementById('cut-gl');
  if (!heroEl || !supportsGL()) return;

  let gltf;
  try {
    gltf = await new GLTFLoader().loadAsync(heroEl.dataset.src);
  } catch (e) {
    return; // keep the CSS wafer
  }

  const views = [];
  heroEl.parentElement.classList.add('gl-on');
  views.push(new WaferView(heroEl, gltf.scene, 'hero'));
  let cut = null;
  if (cutEl) {
    cutEl.parentElement.classList.add('gl-on');
    cut = new WaferView(cutEl, gltf.scene, 'cut');
    views.push(cut);
  }

  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { const v = views.find((x) => x.el === e.target); if (v) v.visible = e.isIntersecting; });
    });
    views.forEach((v) => io.observe(v.el));
  }
  window.addEventListener('resize', () => views.forEach((v) => v.resize()));

  const tech = document.getElementById('technology');
  const cutWafer = document.getElementById('cut-wafer');
  const tags = cut ? cut.el.parentElement.querySelectorAll('.w-tag') : [];

  let last = performance.now();
  const loop = (now) => {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const t = now / 1000;
    if (cut) {
      const r = tech.getBoundingClientRect();
      const p = clamp(-r.top / (r.height - window.innerHeight), 0, 1);
      cut.explode = ease(clamp(p / 0.18, 0, 1)) * 0.42;
      cut.layer = cutWafer ? cutWafer.dataset.layer : 'all';
    }
    views.forEach((v) => { if (v.visible) v.update(dt, t); });
    if (cut && cut.visible) {
      const show = cut.explode > 0.08;
      const vr = cut.el.parentElement.getBoundingClientRect();
      const er = cut.el.getBoundingClientRect();
      tags.forEach((tag) => {
        const name = LAYERS[tag.dataset.for];
        const pt = cut.edge(name);
        let x = pt.x + er.left - vr.left + 14;
        const y = pt.y + er.top - vr.top - 8;
        x = Math.min(x, vr.width - tag.offsetWidth);
        tag.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px)`;
        tag.style.opacity = show ? '' : '0';
        tag.classList.toggle('is-dim', cut.layer !== 'all' && cut.layer !== 'int' && cut.layer !== tag.dataset.for);
      });
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);
}

start();
