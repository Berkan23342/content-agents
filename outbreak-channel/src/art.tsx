import React from 'react';

// Flat, dark vector art for Outbreak Diary. Everything is drawn on a 1080x1920 canvas.
export const W = 1080;
export const H = 1920;

export const C = {
	sky0: '#05070f',
	sky1: '#0e1530',
	sky2: '#1c2748',
	far: '#141b33',
	near: '#0b1022',
	wall: '#252a3d',
	wall2: '#1c2031',
	floor: '#141724',
	wood: '#3a2a20',
	wood2: '#2c2019',
	warm: '#ffc76a',
	warmGlow: 'rgba(255, 190, 100, 0.55)',
	red: '#ff3b30',
	ink: '#06070b',
	pale: '#d9dde8',
	teal: '#24414a',
	moon: '#f3ecd2',
};

export const hash = (n: number) => {
	const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};
export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** On/off flicker that holds each state for a few frames, like a failing bulb. */
export const flicker = (frame: number, seed: number, onRate = 0.82) => (hash(Math.floor(frame / 3) * 13.7 + seed) < onRate ? 1 : 0.15);

// ---------------------------------------------------------------- shared pieces
export const Defs: React.FC = () => (
	<defs>
		<filter id="blur8" x="-50%" y="-50%" width="200%" height="200%">
			<feGaussianBlur stdDeviation="8" />
		</filter>
		<filter id="blur24" x="-50%" y="-50%" width="200%" height="200%">
			<feGaussianBlur stdDeviation="24" />
		</filter>
		<radialGradient id="warmGlow">
			<stop offset="0%" stopColor="#ffd38a" stopOpacity={0.75} />
			<stop offset="100%" stopColor="#ffb44d" stopOpacity={0} />
		</radialGradient>
		<radialGradient id="coolGlow">
			<stop offset="0%" stopColor="#b9d3ff" stopOpacity={0.45} />
			<stop offset="100%" stopColor="#b9d3ff" stopOpacity={0} />
		</radialGradient>
		<radialGradient id="fireGlow">
			<stop offset="0%" stopColor="#ff8a2a" stopOpacity={0.8} />
			<stop offset="100%" stopColor="#ff5a1f" stopOpacity={0} />
		</radialGradient>
		<radialGradient id="moonGlow">
			<stop offset="20%" stopColor="#f3ecd2" stopOpacity={0.35} />
			<stop offset="100%" stopColor="#f3ecd2" stopOpacity={0} />
		</radialGradient>
		<linearGradient id="nightSky" x1="0" y1="0" x2="0" y2="1">
			<stop offset="0%" stopColor={C.sky0} />
			<stop offset="60%" stopColor={C.sky1} />
			<stop offset="100%" stopColor={C.sky2} />
		</linearGradient>
	</defs>
);

export const Stars: React.FC<{frame: number; n?: number; maxY?: number; seed?: number}> = ({frame, n = 60, maxY = 900, seed = 0}) => (
	<g>
		{Array.from({length: n}, (_, i) => (
			<circle key={i} cx={hash(i + seed) * W} cy={hash(i + 40 + seed) * maxY} r={1 + hash(i + 7) * 2} fill="#dfe6ff" opacity={0.25 + 0.5 * Math.abs(Math.sin(frame / (20 + (i % 9) * 4) + i))} />
		))}
	</g>
);

export const Moon: React.FC<{x: number; y: number; r: number}> = ({x, y, r}) => (
	<g>
		<circle cx={x} cy={y} r={r * 3.2} fill="url(#moonGlow)" />
		<circle cx={x} cy={y} r={r} fill={C.moon} />
		<circle cx={x - r * 0.3} cy={y - r * 0.2} r={r * 0.18} fill="#ddd3b4" />
		<circle cx={x + r * 0.35} cy={y + r * 0.3} r={r * 0.12} fill="#ddd3b4" />
	</g>
);

/** A row of building silhouettes along a baseline, some with a dim window or two. */
export const Skyline: React.FC<{base: number; seed: number; color: string; maxH: number; lit?: number}> = ({base, seed, color, maxH, lit = 0.08}) => {
	const out: React.ReactNode[] = [];
	let x = -20;
	let i = 0;
	while (x < W + 20) {
		const w = 70 + hash(seed + i) * 120;
		const h = maxH * (0.35 + hash(seed + i + 50) * 0.65);
		out.push(<rect key={`b${i}`} x={x} y={base - h} width={w + 2} height={h + 400} fill={color} />);
		for (let k = 0; k < 6; k++) {
			if (hash(seed + i * 7 + k) < lit) {
				out.push(<rect key={`w${i}-${k}`} x={x + 12 + hash(seed + i + k) * (w - 30)} y={base - h + 20 + hash(i + k * 3) * (h - 40)} width={8} height={11} fill="#e8c27a" opacity={0.6} />);
			}
		}
		x += w;
		i++;
	}
	return <g>{out}</g>;
};

/** Columns of smoke drifting up from fires in the distance. */
export const Smoke: React.FC<{frame: number; xs: number[]; base: number; color?: string}> = ({frame, xs, base, color = '#2a2f40'}) => (
	<g filter="url(#blur24)">
		{xs.map((x0, k) =>
			Array.from({length: 7}, (_, i) => {
				const p = ((frame * 0.5 + i * 60 + k * 37) % 420) / 420;
				return <circle key={`${k}-${i}`} cx={x0 + Math.sin(p * 4 + k) * 40 + p * 80} cy={base - p * 900} r={40 + p * 120} fill={color} opacity={0.55 * (1 - p)} />;
			}),
		)}
	</g>
);

export const FireGlow: React.FC<{x: number; y: number; r: number; frame: number}> = ({x, y, r, frame}) => (
	<ellipse cx={x} cy={y} rx={r * (1 + 0.06 * Math.sin(frame / 3))} ry={r * 0.6} fill="url(#fireGlow)" opacity={0.75 + 0.25 * Math.sin(frame / 2.3)} />
);

// ---------------------------------------------------------------- characters
/** A shambling infected, seen from the side; (x, y) is between the feet. */
export const Walker: React.FC<{x: number; y: number; h: number; frame: number; seed?: number; flip?: boolean; color?: string; eyes?: boolean}> = ({
	x,
	y,
	h,
	frame,
	seed = 0,
	flip = false,
	color = C.ink,
	eyes = false,
}) => {
	const u = h / 100;
	const ph = frame * 0.09 + seed * 2.1;
	const a = Math.sin(ph) * 0.32;
	const bob = Math.abs(Math.sin(ph)) * 1.6 * u;
	const hip = {x: 0, y: -48 * u - bob};
	const leg = (s: number) => {
		const ang = a * s;
		const kx = hip.x + Math.sin(ang) * 25 * u;
		const ky = hip.y + Math.cos(ang) * 25 * u;
		const fx = kx + Math.sin(ang * 0.4 - 0.08) * 24 * u;
		return `M${hip.x} ${hip.y} L${kx} ${ky} L${fx} ${-bob * 0.2}`;
	};
	const swing = Math.sin(ph * 0.5 + 1) * 3 * u;
	return (
		<g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1) rotate(${Math.sin(ph * 0.5) * 3})`}>
			<g stroke={color} strokeLinecap="round" strokeLinejoin="round" fill="none">
				<path d={leg(1)} strokeWidth={9 * u} />
				<path d={leg(-1)} strokeWidth={9 * u} />
				<path d={`M${9 * u} ${-77 * u - bob} L${34 * u} ${-70 * u - bob + swing} L${50 * u} ${-67 * u - bob + swing * 1.3}`} strokeWidth={7 * u} />
				<path d={`M${6 * u} ${-76 * u - bob} L${12 * u} ${-56 * u - bob - swing * 0.4} L${16 * u} ${-40 * u - bob}`} strokeWidth={7 * u} />
			</g>
			<path
				d={`M${-8 * u} ${-46 * u - bob} L${-3 * u} ${-41 * u - bob} L${2 * u} ${-47 * u - bob} L${7 * u} ${-42 * u - bob} L${10 * u} ${-48 * u - bob} L${16 * u} ${-80 * u - bob} L${0} ${-83 * u - bob} Z`}
				fill={color}
			/>
			<circle cx={17 * u} cy={-90 * u - bob} r={8.5 * u} fill={color} />
			{eyes ? (
				<>
					<circle cx={21 * u} cy={-91 * u - bob} r={1.3 * u} fill="#e8f0d0" opacity={0.85} />
					<circle cx={24.5 * u} cy={-90.5 * u - bob} r={1.1 * u} fill="#e8f0d0" opacity={0.7} />
				</>
			) : null}
		</g>
	);
};

/** An infected seen from straight above: shoulders and a head. */
export const TopWalker: React.FC<{x: number; y: number; s: number; frame: number; seed: number}> = ({x, y, s, frame, seed}) => {
	const rot = hash(seed) * 360 + Math.sin(frame / 40 + seed) * 12;
	const sway = Math.sin(frame * 0.09 + seed) * 4;
	return (
		<g transform={`translate(${x} ${y}) rotate(${rot})`}>
			<ellipse cx={6} cy={8} rx={30 * s} ry={14 * s} fill="#000" opacity={0.35} />
			<ellipse cx={sway} cy={0} rx={28 * s} ry={12 * s} fill="#161922" stroke="#2c3140" strokeWidth={2.5} />
			<circle cx={sway * 0.6 + 8 * s} cy={0} r={10 * s} fill="#262a35" />
		</g>
	);
};

/** Biscuit, a small scruffy terrier. pose: lie, sleep, sit, alert. (x, y) is the ground under the middle. */
export const Dog: React.FC<{x: number; y: number; s: number; frame: number; pose: string; light?: number}> = ({x, y, s, frame, pose, light = 1}) => {
	const fur = '#c69b6d';
	const dark = '#8a6440';
	const breath = 1 + Math.sin(frame / 14) * 0.02;
	const wag = pose === 'alert' ? Math.sin(frame / 2.2) * 2 : Math.sin(frame / 5) * 10;
	const ear = pose === 'alert' ? -30 : 15 + Math.sin(frame / 37) * 4;
	const shade = `brightness(${0.35 + 0.65 * light})`;
	if (pose === 'lie' || pose === 'sleep') {
		const closed = pose === 'sleep';
		return (
			<g transform={`translate(${x} ${y}) scale(${s})`} style={{filter: shade}}>
				<ellipse cx={0} cy={-6} rx={130} ry={14} fill="#000" opacity={0.3} />
				<path d={`M120 -40 Q170 ${-60 + wag} 175 ${-30 + wag}`} stroke={dark} strokeWidth={14} fill="none" strokeLinecap="round" />
				<ellipse cx={20} cy={-48} rx={115 * breath} ry={44 * breath} fill={fur} />
				<ellipse cx={60} cy={-60} rx={40} ry={22} fill={dark} opacity={0.6} />
				<ellipse cx={-30} cy={-14} rx={46} ry={14} fill={fur} />
				<ellipse cx={-95} cy={-58} rx={52} ry={44} fill={fur} />
				<ellipse cx={-140} cy={-44} rx={30} ry={20} fill="#d8b48a" />
				<circle cx={-166} cy={-50} r={8} fill={C.ink} />
				<path d={`M-80 -96 L${-60 + ear * 0.2} -132 L-52 -88 Z`} fill={dark} />
				{closed ? <path d="M-118 -68 q8 6 16 0" stroke={C.ink} strokeWidth={4} fill="none" /> : <circle cx={-112} cy={-68} r={6} fill={C.ink} />}
			</g>
		);
	}
	const up = pose === 'alert' ? -10 : 0;
	return (
		<g transform={`translate(${x} ${y}) scale(${s})`} style={{filter: shade}}>
			<ellipse cx={0} cy={-4} rx={90} ry={12} fill="#000" opacity={0.3} />
			<path d={`M60 -40 Q100 ${-80 + wag} 90 ${-110 + wag}`} stroke={dark} strokeWidth={14} fill="none" strokeLinecap="round" />
			<rect x={-50} y={-70} width={22} height={70} rx={10} fill={fur} />
			<rect x={30} y={-60} width={22} height={60} rx={10} fill={dark} />
			<ellipse cx={0} cy={-90 + up} rx={78 * breath} ry={58 * breath} fill={fur} />
			<ellipse cx={-48} cy={-158 + up} rx={50} ry={46} fill={fur} />
			<ellipse cx={-86} cy={-144 + up} rx={28} ry={19} fill="#d8b48a" />
			<circle cx={-110} cy={-150 + up} r={8} fill={C.ink} />
			<circle cx={-58} cy={-170 + up} r={6.5} fill={C.ink} />
			<path d={`M-30 -196 L${-14} ${-238 + ear} L-6 -182 Z`} fill={dark} transform={`translate(0 ${up})`} />
		</g>
	);
};

const LOOKS: Record<string, {body: string; skin: string; legs: string}> = {
	okafor: {body: '#5b3f52', skin: '#6e4a3a', legs: '#2b2433'},
	leo: {body: '#2e3f5e', skin: '#6e4a3a', legs: '#1f2a40'},
	dev: {body: '#1f2c48', skin: '#5a3a2c', legs: '#151c2c'},
	ava: {body: '#6a2e3a', skin: '#b88a6c', legs: '#22252f'},
};

/** A person sitting, mostly in shadow. who: okafor (grey bun), leo (hoodie), dev (guard's cap) or ava (ponytail). */
export const Sitter: React.FC<{x: number; y: number; s: number; frame: number; who: string}> = ({x, y, s, frame, who}) => {
	const b = Math.sin(frame / 18) * 2;
	const look = LOOKS[who] ?? LOOKS.okafor;
	const body = look.body;
	const skin = look.skin;
	return (
		<g transform={`translate(${x} ${y}) scale(${s})`}>
			<path d={`M-70 0 Q-80 -150 -40 ${-190 + b} L40 ${-190 + b} Q80 -150 70 0 Z`} fill={body} />
			<path d="M-60 0 L-60 40 L110 40 L120 120 L150 120 L140 10 Z" fill={look.legs} />
			<circle cx={0} cy={-235 + b} r={46} fill={skin} />
			{who === 'dev' ? (
				<>
					<path d={`M-50 ${-250 + b} Q-46 ${-296 + b} 0 ${-294 + b} Q46 ${-296 + b} 50 ${-250 + b} Z`} fill="#141a2b" />
					<rect x={-14} y={-262 + b} width={84} height={12} rx={6} fill="#141a2b" />
					<circle cx={-26} cy={-120 + b} r={9} fill="#c9a24a" />
				</>
			) : who === 'ava' ? (
				<>
					<path d={`M-48 ${-236 + b} Q-50 ${-292 + b} 0 ${-290 + b} Q50 ${-292 + b} 48 ${-236 + b} Q20 ${-266 + b} -48 ${-236 + b} Z`} fill="#3a2418" />
					<path d={`M40 ${-262 + b} Q96 ${-250 + b} ${80 + Math.sin(frame / 11) * 6} ${-190 + b}`} stroke="#3a2418" strokeWidth={22} fill="none" strokeLinecap="round" />
				</>
			) : who === 'leo' ? (
				<path d={`M-56 ${-230 + b} Q-60 ${-300 + b} 0 ${-298 + b} Q60 ${-300 + b} 56 ${-230 + b} L44 ${-210 + b} Q0 ${-280 + b} -44 ${-210 + b} Z`} fill={body} />
			) : (
				<>
					<path d={`M-46 ${-240 + b} Q-40 ${-292 + b} 0 ${-288 + b} Q44 ${-290 + b} 46 ${-238 + b} Q20 ${-262 + b} -46 ${-240 + b} Z`} fill="#b9b6b0" />
					<circle cx={0} cy={-300 + b} r={22} fill="#b9b6b0" />
				</>
			)}
		</g>
	);
};
