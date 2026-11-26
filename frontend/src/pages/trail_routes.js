        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "巡查路线与入口",
  "module": "路线档案",
  "caption": "路线档案",
  "detail": "每条路线保存独立的入口码与领班名额。负责人可停用后续领班，既有签到资料保留。",
  "path": "/trail_routes",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "name",
      "label": "堤线名称"
    },
    {
      "name": "checkpoint",
      "label": "扫码检查点"
    },
    {
      "name": "max_leads",
      "label": "每潮窗带队名额"
    },
    {
      "name": "active",
      "label": "开放排班"
    }
  ],
  "layout": "flip",
  "view": "stack",
  "actions": [
    {
      "name": "register_route",
      "label": "登记堤线路线",
      "path": "/trail_routes/register-route",
      "fields": [
        {
          "name": "code",
          "label": "路线编号",
          "kind": "text",
          "initial": "TR-D"
        },
        {
          "name": "name",
          "label": "堤线名称",
          "kind": "text",
          "initial": "东礁折线"
        },
        {
          "name": "checkpoint",
          "label": "检查点编号",
          "kind": "text",
          "initial": "GATE-REEF"
        },
        {
          "name": "max_leads",
          "label": "每潮窗名额",
          "kind": "int",
          "initial": 1
        }
      ],
      "help": "现场检查点与唯一入口码对应。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "pause_route",
      "label": "停止路线排班",
      "path": "/trail_routes/pause-route",
      "fields": [
        {
          "name": "route",
          "label": "路线编号",
          "kind": "text",
          "initial": "TR-D"
        }
      ],
      "help": "禁用后无法对这条线新建窗口、领班或签到。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "trail_routes";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
