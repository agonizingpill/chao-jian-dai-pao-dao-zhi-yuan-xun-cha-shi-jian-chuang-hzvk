        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "志愿者领班和检查点签收",
  "module": "带队与签到",
  "caption": "带队与签到",
  "detail": "带队员按名额和潮窗领班，到指定入口时签到，再由负责人签回。封闭状态在签到时重新核查。",
  "path": "/lead_shifts",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "window",
      "label": "关联潮窗"
    },
    {
      "name": "lead",
      "label": "带队员"
    },
    {
      "name": "contact",
      "label": "队内联络号"
    },
    {
      "name": "on_site",
      "label": "到场时间 UTC+8"
    },
    {
      "name": "checkpoint",
      "label": "签到检查点"
    },
    {
      "name": "state",
      "label": "交接状态"
    }
  ],
  "layout": "stack",
  "view": "table",
  "actions": [
    {
      "name": "assign_lead",
      "label": "确认志愿者领班",
      "path": "/lead_shifts/assign-lead",
      "fields": [
        {
          "name": "code",
          "label": "领班号",
          "kind": "text",
          "initial": "SHIFT-QA"
        },
        {
          "name": "window",
          "label": "潮窗编号",
          "kind": "text",
          "initial": "WINDOW-QA"
        },
        {
          "name": "lead",
          "label": "带队员",
          "kind": "text",
          "initial": "温河"
        },
        {
          "name": "contact",
          "label": "队内联络号",
          "kind": "text",
          "initial": "TD-030"
        }
      ],
      "help": "检查路线开放状态和窗口中的剩余名额。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "check_in",
      "label": "检查点签到",
      "path": "/lead_shifts/check-in",
      "fields": [
        {
          "name": "shift",
          "label": "领班号",
          "kind": "text",
          "initial": "SHIFT-QA"
        },
        {
          "name": "checkpoint",
          "label": "扫码检查点",
          "kind": "text",
          "initial": "GATE-EAST"
        },
        {
          "name": "arrived_at",
          "label": "到场时间 · YYYY-MM-DD HH:MM",
          "kind": "text",
          "initial": "2090-12-15 00:11"
        }
      ],
      "help": "记录本次演练的检查点扫码时间。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "hand_back",
      "label": "负责人签回班次",
      "path": "/lead_shifts/hand-back",
      "fields": [
        {
          "name": "shift",
          "label": "领班号",
          "kind": "text",
          "initial": "SHIFT-QA"
        }
      ],
      "help": "签回后旧记录仍可读取，名额释放。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "lead_shifts";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
