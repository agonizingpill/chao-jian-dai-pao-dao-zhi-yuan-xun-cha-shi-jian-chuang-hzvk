import {request} from './api.js';
import {el} from './dom.js';

const duration = 4 * 60;
const left = 22 * 60;

function normalizedStart(window) {
  const start = window.opening_minute + (window.opening_minute < duration / 2 ? 1440 : 0);
  return start - left;
}

export async function timeline(root) {
  const rows = await request('/patrol_windows');
  const panel = el('section', {class: 'patrol-timeline', 'aria-label': '跨午夜相位图'},
    el('h2', {}, '跨午夜相位图'),
    el('p', {}, '按 UTC+8 将 22:00 至次日 02:00 的潮窗叠放。绝对日期见窗口台账。'),
    el('div', {class: 'ticks'}, el('span', {}, '22:00'), el('span', {}, '次日 00:00'), el('span', {}, '02:00')));
  for (const item of rows) {
    const minute = normalizedStart(item);
    const start = Math.max(0, minute);
    const end = Math.min(duration, minute + item.minutes);
    if (start >= end || minute < -180 || minute >= duration) continue;
    const bar = el('span', {});
    bar.style.setProperty('--start', start / duration * 100 + '%');
    bar.style.setProperty('--span', (end - start) / duration * 100 + '%');
    panel.append(el('article', {},
      el('strong', {}, item.code), el('div', {class: 'night-axis', 'aria-hidden': 'true'}, bar),
      el('time', {}, item.opens.slice(11, 16) + '–' + item.closes.slice(11, 16))));
  }
  const ledger = root.querySelector('.ledger');
  if (ledger) ledger.before(panel);
}
