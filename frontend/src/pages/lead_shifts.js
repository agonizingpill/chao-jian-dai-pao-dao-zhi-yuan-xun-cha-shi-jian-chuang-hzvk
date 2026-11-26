import {workspace} from '../workspace.js';
import {el} from '../dom.js';
import {request} from '../api.js';
import {session} from '../store.js';

const page = {
  "title": "志愿者领班和检查点签收",
  "module": "带队与签到",
  "caption": "带队与签到",
  "detail": "带队员按名额和潮窗领班，到指定入口时签到，再由负责人签回。带队页用圆周相位距离找同路、同潮相且开窗前已结束的已交回近邻班次，估算到场时刻；值班员可试调距离权重，按同一批冻结样本回放后决定是否一起启用。",
  "path": "/lead_shifts",
  "columns": [
    {"name": "code", "label": "编号"},
    {"name": "window", "label": "关联潮窗"},
    {"name": "lead", "label": "带队员"},
    {"name": "contact", "label": "队内联络号"},
    {"name": "on_site", "label": "到场时间 UTC+8"},
    {"name": "checkpoint", "label": "签到检查点"},
    {"name": "state", "label": "交接状态"}
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "estimate_arrival",
      "label": "圆周近邻估算到场时刻",
      "path": "/lead_shifts/estimate-arrival",
      "fields": [
        {"name": "shift", "label": "领班号或潮窗编号", "kind": "text", "initial": "SHIFT-ARCHIVE"}
      ],
      "help": "只取同路线、同潮相、其潮窗在目标开窗前已结束的已交回班次；估算始终使用当前已启用的距离权重。",
      "roles": ["operator", "reviewer", "viewer"],
      "success": "估算完成"
    },
    {
      "name": "trial_weights",
      "label": "试调距离权重并发起试评",
      "path": "/lead_shifts/trial-weights",
      "fields": [
        {"name": "phase_weight", "label": "圆周相位（弦长）权重", "kind": "float", "initial": 0.5},
        {"name": "duration_weight", "label": "窗口时长差权重", "kind": "float", "initial": 2}
      ],
      "help": "新旧权重回放同一批发起时冻结的已交回样本。发起时开放的路线 MAE 都不升且至少一路下降，才一起启用；缺可回放班次即暂缓。",
      "roles": ["operator", "reviewer"],
      "success": "试评已提交"
    },
    {
      "name": "resume_trial",
      "label": "恢复/立即处理试评任务",
      "path": "/lead_shifts/resume-trial",
      "fields": [
        {"name": "token", "label": "试评计算任务号（自动带入最近任务）", "kind": "token", "initial": ""}
      ],
      "help": "中断恢复仍按试评单冻结的原样本计算；若期间已有别的试评启用新权重，会拿原样本跟当前新版权重重比。",
      "roles": ["operator", "reviewer"],
      "success": "试评已处理"
    },
    {
      "name": "assign_lead",
      "label": "确认志愿者领班",
      "path": "/lead_shifts/assign-lead",
      "fields": [
        {"name": "code", "label": "领班号", "kind": "text", "initial": "SHIFT-QA"},
        {"name": "window", "label": "潮窗编号", "kind": "text", "initial": "WINDOW-QA"},
        {"name": "lead", "label": "带队员", "kind": "text", "initial": "温河"},
        {"name": "contact", "label": "队内联络号", "kind": "text", "initial": "TD-030"}
      ],
      "help": "检查路线开放状态和窗口中的剩余名额。",
      "roles": ["operator", "reviewer"],
      "success": "已写入"
    },
    {
      "name": "check_in",
      "label": "检查点签到",
      "path": "/lead_shifts/check-in",
      "fields": [
        {"name": "shift", "label": "领班号", "kind": "text", "initial": "SHIFT-QA"},
        {"name": "checkpoint", "label": "扫码检查点", "kind": "text", "initial": "GATE-EAST"},
        {"name": "arrived_at", "label": "到场时间 · YYYY-MM-DD HH:MM", "kind": "text", "initial": "2090-12-15 00:11"}
      ],
      "help": "记录本次演练的检查点扫码时间。",
      "roles": ["operator", "reviewer"],
      "success": "已写入"
    },
    {
      "name": "hand_back",
      "label": "负责人签回班次",
      "path": "/lead_shifts/hand-back",
      "fields": [
        {"name": "shift", "label": "领班号", "kind": "text", "initial": "SHIFT-QA"}
      ],
      "help": "签回后旧记录仍可读取，名额释放；可补 ended_at 演练结束时刻。",
      "roles": ["reviewer"],
      "success": "已写入"
    }
  ]
};

function fmt(value, digits = 3) {
  return typeof value === 'number' ? value.toFixed(digits) : '—';
}

function maeTable(trial) {
  const rows = trial.route_reports || [];
  if (!rows.length) return null;
  return el('table', {},
    el('thead', {}, el('tr', {},
      el('th', {scope: 'col'}, '路线'), el('th', {scope: 'col'}, '样本'),
      el('th', {scope: 'col'}, 'MAE 在用'), el('th', {scope: 'col'}, 'MAE 试调'),
      el('th', {scope: 'col'}, '变化'))),
    el('tbody', {}, rows.map(r => el('tr', {},
      el('td', {}, r.route),
      el('td', {}, String(trial.sample_count ?? '')),
      el('td', {}, fmt(r.mae_before)),
      el('td', {}, fmt(r.mae_after)),
      el('td', {}, r.delta === null || r.delta === undefined ? '—'
        : (r.delta <= 0 ? '↓ ' : '↑ ') + fmt(Math.abs(r.delta)))))));
}

function trialCard(trial, role, reload) {
  const stateClass = 'state state-' + (trial.status || 'queued');
  const card = el('article', {class: 'trial'},
    el('header', {},
      el('h3', {}, trial.code),
      el('span', {class: stateClass}, trial.state),
      el('span', {}, '样本 ' + (trial.sample_count ?? 0)),
      el('span', {}, '圆周权重 ' + fmt(trial.proposed?.phase, 2)
        + ' / 时长权重 ' + fmt(trial.proposed?.duration, 2))));
  if (trial.detail) card.append(el('p', {}, trial.detail));
  const table = maeTable(trial);
  if (table) card.append(table);
  if (trial.routes?.length) card.append(el('p', {}, '发起时开放路线：' + trial.routes.join('、')));
  if ((trial.status === 'queued' || trial.status === 'running')
      && ['operator', 'reviewer'].includes(role)) {
    const button = el('button', {type: 'button'}, '恢复并按原样本处理');
    const notice = el('span', {class: 'status'}, '');
    button.addEventListener('click', async () => {
      button.disabled = true;
      try {
        await request('/lead_shifts/resume-trial', {code: trial.code});
        await reload();
      } catch (error) {
        notice.textContent = error.message;
        button.disabled = false;
      }
    });
    card.append(el('div', {}, button, notice));
  }
  return card;
}

async function weightLab(root) {
  const role = session()?.role;
  const current = el('div', {class: 'weights-current'}, '读取已启用权重…');
  const trials = el('div', {class: 'trials'}, '');
  const panel = el('section', {class: 'weight-lab', 'aria-label': '距离权重试评台账'},
    el('h2', {}, '距离权重与试评台账'), current,
    el('div', {class: 'actions'},
      el('button', {type: 'button', id: 'lab-refresh'}, '刷新台账')),
    el('h3', {}, '试评单'), trials);
  root.append(panel);

  async function reload() {
    try {
      const weights = await request('/lead_shifts/weights');
      current.replaceChildren(
        el('strong', {}, '预估当前照用：'),
        el('span', {}, '圆周相位权重 ' + weights.phase_weight),
        el('span', {}, '时长差权重 ' + weights.duration_weight),
        el('span', {}, '近邻数 ' + (weights.neighbor_count || 5)));
      const list = await request('/lead_shifts/weight-trials');
      trials.replaceChildren();
      if (!list.length) {
        trials.append(el('p', {class: 'status'}, '暂无试评单。提交试调权重后在此回放。'));
        return;
      }
      list.reverse().forEach(trial => trials.append(trialCard(trial, role, reload)));
    } catch (error) {
      current.textContent = error.message;
    }
  }
  panel.querySelector('#lab-refresh').addEventListener('click', reload);
  document.addEventListener('lab:changed', reload, {once: true});
  await reload();
}

export const {title} = page;
export const key = "lead_shifts";
export async function render(root, role) {
  await workspace(root, role, page);
  await weightLab(root, role);
}
