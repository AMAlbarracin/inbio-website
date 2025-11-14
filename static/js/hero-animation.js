// static/js/hero-animation.js
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.157.0/build/three.module.js';

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ alpha: true });

renderer.setSize(window.innerWidth, 400);
document.getElementById('hero-canvas').appendChild(renderer.domElement);

// Crear molécula de ADN simple
const geometry = new THREE.TorusGeometry(1, 0.3, 16, 100);
const material = new THREE.MeshBasicMaterial({ color: 0x64ffda });
const dna = new THREE.Mesh(geometry, material);
scene.add(dna);

camera.position.z = 5;

function animate() {
    requestAnimationFrame(animate);
    dna.rotation.x += 0.01;
    dna.rotation.y += 0.01;
    renderer.render(scene, camera);
}
animate();
