import React from 'react';
import {AbsoluteFill, continueRender, delayRender, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

// Same design language as makulbul.com (public/index.html :root) and the mobile app theme.
export const C = {
	bg: '#0a0a0e',
	surface: '#16171f',
	surface2: '#1e202b',
	border: '#2a2c38',
	text: '#edeef3',
	muted: '#9a9db0',
	signal: '#7c82ff',
	signalSoft: '#1b1c3d',
	deal: '#c8ff4d',
	dealInk: '#12140a',
	danger: '#ff6b6b',
};

export const DISPLAY = 'Space Grotesk';
export const BODY = 'Inter';
export const MONO = 'IBM Plex Mono';

// fonts ship with the project (OFL, copied from the mobile app's @expo-google-fonts), so renders need no network
const FONTS: [string, string, string][] = [
	[DISPLAY, 'SpaceGrotesk_700Bold.ttf', '700'],
	[DISPLAY, 'SpaceGrotesk_600SemiBold.ttf', '600'],
	[BODY, 'Inter_500Medium.ttf', '500'],
	[BODY, 'Inter_700Bold.ttf', '700'],
	[BODY, 'Inter_800ExtraBold.ttf', '800'],
	[MONO, 'IBMPlexMono_600SemiBold.ttf', '600'],
];
if (typeof document !== 'undefined') {
	const handle = delayRender('Loading brand fonts');
	Promise.all(
		FONTS.map(([family, file, weight]) => {
			const face = new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, {weight});
			return face.load().then((f) => document.fonts.add(f));
		}),
	).then(() => continueRender(handle));
}

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));

/** Springs from 0 to 1 starting at `at` (frames). */
export const useIn = (at: number, damping = 14) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	return spring({frame: frame - at, fps, config: {damping, stiffness: 160}});
};

export const Logo: React.FC<{size?: number}> = ({size = 44}) => (
	<div style={{display: 'flex', alignItems: 'center', gap: size * 0.3, fontFamily: DISPLAY, fontWeight: 700, fontSize: size, color: C.text}}>
		<span style={{width: size * 0.42, height: size * 0.42, borderRadius: '50%', background: C.deal, display: 'inline-block'}} />
		Makulbul
	</div>
);

/** Dark backdrop with a slow lime/indigo glow and a faint grid. */
export const Backdrop: React.FC<{accent?: string}> = ({accent = C.signal}) => {
	const frame = useCurrentFrame();
	const drift = Math.sin(frame / 60) * 60;
	return (
		<AbsoluteFill style={{background: C.bg, overflow: 'hidden'}}>
			<div
				style={{
					position: 'absolute',
					width: 1100,
					height: 1100,
					left: -300 + drift,
					top: -350,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${accent}33 0%, transparent 65%)`,
				}}
			/>
			<div
				style={{
					position: 'absolute',
					width: 1000,
					height: 1000,
					right: -350 - drift,
					bottom: -300,
					borderRadius: '50%',
					background: `radial-gradient(circle, ${C.deal}22 0%, transparent 65%)`,
				}}
			/>
			<AbsoluteFill
				style={{
					backgroundImage: `linear-gradient(${C.border}55 1px, transparent 1px), linear-gradient(90deg, ${C.border}55 1px, transparent 1px)`,
					backgroundSize: '90px 90px',
					opacity: 0.35,
				}}
			/>
		</AbsoluteFill>
	);
};

/** Text that slides up and fades in at `at`. */
export const Rise: React.FC<{at: number; children: React.ReactNode; style?: React.CSSProperties; dist?: number}> = ({at, children, style, dist = 60}) => {
	const s = useIn(at);
	return <div style={{...style, opacity: clamp(s * 1.4), transform: `translateY(${(1 - s) * dist}px)`}}>{children}</div>;
};

/** Words of a headline pop in one after another. */
export const Headline: React.FC<{text: string; at: number; size: number; color?: string; highlight?: string[]; align?: 'left' | 'center'}> = ({
	text,
	at,
	size,
	color = C.text,
	highlight = [],
	align = 'center',
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const words = text.split(' ');
	return (
		<div
			style={{
				fontFamily: DISPLAY,
				fontWeight: 700,
				fontSize: size,
				lineHeight: 1.04,
				letterSpacing: '-0.03em',
				color,
				textAlign: align,
				display: 'flex',
				flexWrap: 'wrap',
				justifyContent: align === 'center' ? 'center' : 'flex-start',
				gap: `0 ${size * 0.26}px`,
			}}
		>
			{words.map((w, i) => {
				const s = spring({frame: frame - at - i * 3, fps, config: {damping: 13, stiffness: 190}});
				const hot = highlight.some((h) => w.toLowerCase().includes(h.toLowerCase()));
				return (
					<span key={i} style={{display: 'inline-block', opacity: clamp(s * 1.5), transform: `translateY(${(1 - s) * size * 0.5}px) scale(${0.85 + s * 0.15})`, color: hot ? C.deal : undefined}}>
						{w}
					</span>
				);
			})}
		</div>
	);
};

export const Pill: React.FC<{children: React.ReactNode; color?: string; ink?: string; size?: number}> = ({children, color = C.signalSoft, ink = C.signal, size = 34}) => (
	<span
		style={{
			display: 'inline-block',
			fontFamily: MONO,
			fontWeight: 600,
			fontSize: size,
			letterSpacing: '0.04em',
			textTransform: 'uppercase',
			color: ink,
			background: color,
			border: `2px solid ${ink}55`,
			borderRadius: 999,
			padding: `${size * 0.35}px ${size * 0.8}px`,
		}}
	>
		{children}
	</span>
);

/** Simple device illustration so no product photos (and their copyrights) are needed. */
export const Device: React.FC<{kind: 'telefon' | 'laptop'; label: string; accent: string; width: number}> = ({kind, label, accent, width}) => {
	if (kind === 'laptop') {
		return (
			<svg width={width} height={width * 0.68} viewBox="0 0 300 204">
				<rect x={36} y={8} width={228} height={150} rx={12} fill={C.surface2} stroke={accent} strokeWidth={5} />
				<rect x={50} y={22} width={200} height={122} rx={6} fill={`${accent}22`} />
				<path d="M8 168 L292 168 L276 196 L24 196 Z" fill={C.surface2} stroke={accent} strokeWidth={5} strokeLinejoin="round" />
				<text x={150} y={92} textAnchor="middle" fontFamily={DISPLAY} fontWeight={700} fontSize={26} fill={C.text}>
					{label}
				</text>
			</svg>
		);
	}
	return (
		<svg width={width} height={width * 1.9} viewBox="0 0 160 304">
			<rect x={6} y={6} width={148} height={292} rx={28} fill={C.surface2} stroke={accent} strokeWidth={5} />
			<rect x={18} y={18} width={124} height={268} rx={20} fill={`${accent}1f`} />
			<rect x={60} y={26} width={40} height={10} rx={5} fill={C.bg} />
			<text x={80} y={160} textAnchor="middle" fontFamily={DISPLAY} fontWeight={700} fontSize={30} fill={C.text}>
				{label}
			</text>
		</svg>
	);
};
