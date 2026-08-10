/**
 * Theme Cycler — Keyboard shortcuts to cycle through available themes
 *
 * Shortcuts:
 *   Ctrl+X          — Cycle theme forward
 *   Ctrl+Q          — Cycle theme backward
 *
 * Commands:
 *   /theme          — Open select picker to choose a theme
 *   /theme <name>   — Switch directly by name
 *
 * Features:
 *   - Status line shows current theme name with accent color
 *   - Color swatch widget flashes briefly after each switch
 *   - Auto-dismisses swatch after 3 seconds
 *
 * Usage: pi -e extensions/theme-cycler.ts -e extensions/minimal.ts
 */

import type { ExtensionAPI, ExtensionContext } from "@mariozechner/pi-coding-agent";
import { truncateToWidth } from "@mariozechner/pi-tui";

export default function (pi: ExtensionAPI) {
	let currentCtx: ExtensionContext | undefined;
	let swatchTimer: ReturnType<typeof setTimeout> | null = null;

	function updateStatus(ctx: ExtensionContext) {
		if (!ctx.hasUI) return;
		const name = ctx.ui.theme.name;
		// 操作名为 "theme" 的状态栏项
		ctx.ui.setStatus("theme", `🎨 ${name} 🎨`);
	}

	function showSwatch(ctx: ExtensionContext) {
		if (!ctx.hasUI) return;

		if (swatchTimer) {
			clearTimeout(swatchTimer);
			swatchTimer = null;
		}

		ctx.ui.setWidget(
			"theme-swatch", // 注册用的唯一名称
			(_tui, theme) => ({ // 工厂函数,返回一个Widget对象的函数,定义组件的渲染行为
				invalidate() { }, // 通知机制,如果组件的数据发生了变化,调用这个方法告诉UI系统本组件需要重新绘制
				render(width: number): string[] { // 渲染函数, width 是系统传入的当前可用宽度
					const block = "\u2588\u2588\u2588";
					const swatch =
						theme.fg("success", block) +
						" " +
						theme.fg("accent", block) +
						" " +
						theme.fg("warning", block) +
						" " +
						theme.fg("dim", block) +
						" " +
						theme.fg("muted", block);
					const label = theme.fg("accent", " 🎨 ") + theme.fg("muted", ctx.ui.theme.name) + "  " + swatch; // fg=Foreground
					const border = theme.fg("borderMuted", "─".repeat(Math.max(0, width)));
					return [border, truncateToWidth("  " + label, width), border]; // 必须返回字符串数组,每个元素代表终端界面上的一行
					// truncateToWidth 的作用是将字符串截断，使其在终端或等宽字体环境下不超过指定的显示宽度
				},
			}),
			{ placement: "belowEditor" }, // 配置选项
		);

		swatchTimer = setTimeout(() => {
			ctx.ui.setWidget("theme-swatch", undefined); // 设置特定组件第二个参数为 undefined,即可更新或删除组件
			swatchTimer = null;
		}, 3000);
	}

	function getThemeList(ctx: ExtensionContext) {
		return ctx.ui.getAllThemes();
	}

	function findCurrentIndex(ctx: ExtensionContext): number {
		const themes = getThemeList(ctx);
		const current = ctx.ui.theme.name;
		return themes.findIndex((t) => t.name === current);
	}

	function cycleTheme(ctx: ExtensionContext, direction: 1 | -1) {
		if (!ctx.hasUI) return;

		const themes = getThemeList(ctx);
		if (themes.length === 0) {
			ctx.ui.notify("No themes available", "warning");
			return;
		}

		let index = findCurrentIndex(ctx);
		if (index === -1) index = 0;

		index = (index + direction + themes.length) % themes.length;
		const theme = themes[index];
		const result = ctx.ui.setTheme(theme.name);

		if (result.success) {
			updateStatus(ctx);
			showSwatch(ctx);
			ctx.ui.notify(`${theme.name} (${index + 1}/${themes.length})`, "info");
		} else {
			ctx.ui.notify(`Failed to set theme: ${result.error}`, "error");
		}
	}

	// --- Shortcuts ---

	pi.registerShortcut("ctrl+x", {
		description: "Cycle theme forward",
		handler: async (ctx) => {
			currentCtx = ctx;
			cycleTheme(ctx, 1);
		},
	});

	pi.registerShortcut("ctrl+q", {
		description: "Cycle theme backward",
		handler: async (ctx) => {
			currentCtx = ctx;
			cycleTheme(ctx, -1);
		},
	});

	// --- Command: /theme ---

	pi.registerCommand("theme", {
		description: "Select a theme: /theme or /theme <name>",
		handler: async (args, ctx) => {
			currentCtx = ctx;
			if (!ctx.hasUI) return;

			const themes = getThemeList(ctx);
			const arg = args.trim(); // 命令，比如 /theme 空格后的字符串都是 arg，这里主要是做首尾whitespace的去除

			if (arg) {
				const result = ctx.ui.setTheme(arg);
				if (result.success) {
					updateStatus(ctx);
					showSwatch(ctx);
					ctx.ui.notify(`Theme: ${arg}`, "info");
				} else {
					ctx.ui.notify(`Theme not found: ${arg}. Use /theme to see available themes.`, "error");
				}
				return;
			}

			const items = themes.map((t) => {
				const desc = t.path ? t.path : "built-in";
				const active = t.name === ctx.ui.theme.name ? " (active)" : "";
				return `${t.name}${active} — ${desc}`;
			});

			const selected = await ctx.ui.select("Select Theme", items); // ctx.ui.select(...) 在 TUI 上渲染列表，并等待用户选择
			if (!selected) return; // 防御性编程

			const selectedName = selected.split(/\s/)[0]; // 获取到 theme 部分的字符串片段
			const result = ctx.ui.setTheme(selectedName); // 设置主题
			if (result.success) {
				updateStatus(ctx);
				showSwatch(ctx);
				ctx.ui.notify(`Theme: ${selectedName}`, "info");
			}
		},
	});

	// --- Session init ---

	pi.on("session_start", async (_event, ctx) => {
		currentCtx = ctx;
		updateStatus(ctx);
	});

	pi.on("session_shutdown", async () => {
		if (swatchTimer) {
			clearTimeout(swatchTimer);
			swatchTimer = null;
		}
	});
}
