        import {workspace} from '../workspace.js';
        import {timeline} from '../nightline.js';

        const page = {
  "title": "跨午夜潮窗与历史相位",
  "module": "潮窗日历",
  "caption": "潮窗日历",
  "detail": "已批准的志愿者工作时间来自排班日历。正余弦由日内相位拟合历史邻近窗口，便于查找同类交接。",
  "path": "/patrol_windows",
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
      "name": "opens",
      "label": "签到起点 UTC+8"
    },
    {
      "name": "closes",
      "label": "签到截止 UTC+8"
    },
    {
      "name": "opening_minute",
      "label": "日内相位分钟"
    },
    {
      "name": "minutes",
      "label": "窗口时长"
    },
    {
      "name": "phase",
      "label": "日历相位"
    },
    {
      "name": "tag",
      "label": "来源凭证"
    }
  ],
  "layout": "split",
  "view": "table",
  "actions": [
    {
      "name": "register_window",
      "label": "登记跨日潮窗",
      "path": "/patrol_windows/register-window",
      "fields": [
        {
          "name": "code",
          "label": "潮窗编号",
          "kind": "text",
          "initial": "WINDOW-QA"
        },
        {
          "name": "route",
          "label": "路线编号",
          "kind": "text",
          "initial": "TR-A"
        },
        {
          "name": "starts_at",
          "label": "签到起点 · YYYY-MM-DD HH:MM",
          "kind": "text",
          "initial": "2090-12-14 23:58"
        },
        {
          "name": "ends_at",
          "label": "签到截止 · YYYY-MM-DD HH:MM",
          "kind": "text",
          "initial": "2090-12-15 00:36"
        },
        {
          "name": "phase",
          "label": "潮汐相位",
          "kind": "text",
          "initial": "落潮"
        },
        {
          "name": "tag",
          "label": "日历凭证",
          "kind": "text",
          "initial": "TIDE-REPLAY-14"
        }
      ],
      "help": "从日历抄录区域窗口。跨午夜时结束日期必须填写次日。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    },
    {
      "name": "compare_phase",
      "label": "计算历史相似潮窗",
      "path": "/patrol_windows/compare-phase",
      "fields": [
        {
          "name": "window",
          "label": "目标潮窗",
          "kind": "text",
          "initial": "WINDOW-QA"
        }
      ],
      "help": "后台将当日开始点嵌入圆周，午夜两侧的时段保持相邻。",
      "roles": [
        "operator",
        "reviewer"
      ],
      "success": "已写入"
    }
  ]
};

        export const {title} = page;
        export const key = "patrol_windows";
        export async function render(root, role) {
          await workspace(root, role, page);
          await timeline(root);

        }
