        import {workspace} from '../workspace.js';
        import {el} from '../dom.js';

        const page = {
  "title": "路线封闭时段",
  "module": "路线限制",
  "caption": "路线限制",
  "detail": "封闭通知绑定路线和绝对日期，可跨午夜，生效后挡住该时点签到。现场签注后才允许解封。",
  "path": "/trail_notices",
  "columns": [
    {
      "name": "code",
      "label": "编号"
    },
    {
      "name": "route",
      "label": "路线"
    },
    {
      "name": "begins",
      "label": "封闭开始 UTC+8"
    },
    {
      "name": "until",
      "label": "封闭结束 UTC+8"
    },
    {
      "name": "reason",
      "label": "封闭缘由"
    },
    {
      "name": "status",
      "label": "限制状态"
    }
  ],
  "layout": "flip",
  "view": "grid",
  "actions": [
    {
      "name": "post_closure",
      "label": "登记路线封闭",
      "path": "/trail_notices/post-closure",
      "fields": [
        {
          "name": "code",
          "label": "封闭号",
          "kind": "text",
          "initial": "BAN-QA"
        },
        {
          "name": "route",
          "label": "路线编号",
          "kind": "text",
          "initial": "TR-A"
        },
        {
          "name": "begins",
          "label": "封闭开始 · YYYY-MM-DD HH:MM",
          "kind": "text",
          "initial": "2090-12-15 00:05"
        },
        {
          "name": "until",
          "label": "封闭结束 · YYYY-MM-DD HH:MM",
          "kind": "text",
          "initial": "2090-12-15 00:20"
        },
        {
          "name": "reason",
          "label": "封闭缘由",
          "kind": "text",
          "initial": "移动护栏换岗"
        }
      ],
      "help": "临时封闭落到绝对时间区间。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "lift_closure",
      "label": "凭见证解封",
      "path": "/trail_notices/lift-closure",
      "fields": [
        {
          "name": "notice",
          "label": "封闭号",
          "kind": "text",
          "initial": "BAN-QA"
        },
        {
          "name": "witness",
          "label": "解封人签注",
          "kind": "text",
          "initial": "秦理 · 现场确认"
        }
      ],
      "help": "解封留痕保留原有缘由。",
      "roles": [
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "trail_notices";
        export async function render(root, role) {
          await workspace(root, role, page);

        }
