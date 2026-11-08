import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Background, Birds, Cloud, LEAVES, Land, LandColors, Look, PopWord, RAINBOW, Weather, blinkAt, textStyle} from './common';
import {Pose} from './critter';
import {Character, EggView, Hero, HeroView, Pop, SpeechBubble} from './hero';
import {Icon} from './library';
import {mix} from './shapes';

// ---------------------------------------------------------------- scene data (written by scripts/fun.py)
export type Bg = 'day' | 'park' | 'farm' | 'forest' | 'pond' | 'dusk' | 'night' | 'rain' | 'party' | 'beach' | 'garden' | 'playground' | 'bedroom' | 'underwater';
type Key = {t: number; x: number; y: number};
type Act = {t: number; kind: 'jump' | 'shake' | 'spin' | 'sleep' | 'wake' | 'wave'};
type Actor = {hero: Hero; size: number; keys: Key[]; acts: Act[]; fly?: boolean; from?: number; until?: number; talk?: {at: number; m: string}[]};
type Prop = {hero: Hero; size: number; keys: Key[]; at: number; until?: number; float?: boolean};
type Bubble = {actor: number; text: string; color: string; at: number; until: number};
type Timed = {text: string; color: string; at: number};

export type FunScene =
	| {type: 'title'; from: number; duration: number; bg: Bg; top: string; title: string[]; heroes: Hero[]; topColor?: string; rays?: string}
	| {
			type: 'story';
			from: number;
			duration: number;
			bg: Bg;
			actors: Actor[];
			props: Prop[];
			bubbles: Bubble[];
			title?: {text: string; at: number; until: number} | null;
			cam?: CamKey[];
	  }
	| {type: 'egg'; from: number; duration: number; bg: Bg; egg: Hero; ticks: number[]; openAt: number; hero: Hero; name: Timed; bubble?: Timed | null}
	| {type: 'shadow'; from: number; duration: number; bg: Bg; hero: Hero; counts: number[]; revealAt: number; name: Timed; bubble?: Timed | null}
	| {
			type: 'dance';
			from: number;
			duration: number;
			bg: Bg;
			beat0: number;
			bpm: number;
			crew: Hero[];
			formation: 'line' | 'wave' | 'center' | 'circle' | 'conga';
			moves: string[];
			callouts: Timed[];
			freezes: {at: number; until: number}[];
	  };

/** While a line is spoken, the camera leans towards the speaker standing at x (written by scripts/fun.py). */
export type CamKey = {at: number; until: number; x: number};

/** Where the camera looks (x) and how much it leans in (0-1) at frame f of a story shot, eased so it never jumps. */
export const storyCam = (keys: CamKey[] | undefined, f: number): {x: number; lean: number} => {
	if (!keys || keys.length === 0) return {x: 960, lean: 0};
	let x = keys[0].x;
	let prevX = keys[0].x;
	let since = 1e9;
	let talking = 0;
	for (const k of keys) {
		if (k.at > f) break;
		prevX = x;
		x = k.x;
		since = f - k.at;
		talking = f < k.until + 10 ? 1 : Math.max(0, 1 - (f - k.until - 10) / 20);
	}
	const e = Math.min(1, since / 14);
	const s = e * e * (3 - 2 * e);
	const into = Math.min(1, since / 14);
	return {x: prevX + (x - prevX) * s, lean: talking * into};
};

// ---------------------------------------------------------------- helpers
const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const hash = (n: number) => {
	const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
	return x - Math.floor(x);
};

const NIGHT_LAND: LandColors = {far: '#2a3f6e', farTree: '#22355f', mid: ['#1f4a52', '#173a42'], front: ['#1a3d3a', '#122e2c'], tuft: '#0f2624', flowers: false};
const DUSK_LAND: LandColors = {far: '#d9a07a', farTree: '#c48a66', mid: ['#8fbf5e', '#6e9e45'], front: ['#5f9a3e', '#4a8230'], tuft: '#3d7028', flowers: true};
const RAIN_LAND: LandColors = {far: '#9fb8b0', farTree: '#8aa69c', mid: ['#7cae62', '#649a4c'], front: ['#5c9a48', '#4a853a'], tuft: '#3e7432', flowers: true};

const Stars: React.FC<{count: number; frame: number; maxY?: number}> = ({count, frame, maxY = 620}) => (
	<>
		{Array.from({length: count}, (_, i) => {
			const x = hash(i) * 1920;
			const y = 20 + hash(i + 50) * maxY;
			const tw = 0.4 + 0.6 * Math.abs(Math.sin(frame / (14 + (i % 7) * 3) + i));
			const r = 2.5 + hash(i + 99) * 4;
			return i % 6 === 0 ? (
				<path
					key={i}
					d={`M${x} ${y - r * 3} Q${x} ${y} ${x + r * 3} ${y} Q${x} ${y} ${x} ${y + r * 3} Q${x} ${y} ${x - r * 3} ${y} Q${x} ${y} ${x} ${y - r * 3}Z`}
					fill="#fff8c8"
					opacity={tw}
				/>
			) : (
				<circle key={i} cx={x} cy={y} r={r} fill="#fff8c8" opacity={tw} />
			);
		})}
	</>
);

/** A round leafy tree; (x, y) is the bottom of the trunk. Outside spring its leaves take the season's colours. */
const Tree: React.FC<{x: number; y: number; s: number; color?: string}> = ({x, y, s, color: given = '#3fae4f'}) => {
	const {season} = React.useContext(Look);
	const color = season === 'spring' ? given : LEAVES[season][Math.round(x) % 3];
	return (
	<svg style={{position: 'absolute', left: x - 130 * s, top: y - 380 * s, overflow: 'visible'}} width={260 * s} height={380 * s} viewBox="0 0 260 380">
		<path d="M112 380 L116 220 Q100 190 84 176 M146 380 L142 220 Q160 196 178 186" stroke="#7a4a28" strokeWidth={14} fill="none" strokeLinecap="round" />
		<path d="M108 380 Q114 300 112 210 L148 210 Q144 300 152 380 Z" fill="#8a5a33" />
		<path d="M126 360 Q124 320 128 290 M136 270 Q138 250 134 236" stroke="#6e4424" strokeWidth={4} fill="none" strokeLinecap="round" />
		<circle cx={130} cy={140} r={112} fill={mix(color, '#000000', 0.15)} />
		<circle cx={66} cy={176} r={72} fill={mix(color, '#000000', 0.1)} />
		<circle cx={194} cy={176} r={72} fill={mix(color, '#000000', 0.1)} />
		<circle cx={130} cy={124} r={100} fill={color} />
		<circle cx={80} cy={160} r={58} fill={color} />
		<circle cx={182} cy={160} r={58} fill={color} />
		<circle cx={98} cy={84} r={34} fill="#fff" opacity={0.16} />
		{[
			[90, 130],
			[170, 110],
			[140, 190],
		].map(([cx, cy]) => (
			<circle key={cx} cx={cx} cy={cy} r={9} fill={season === 'autumn' ? '#ffcf3f' : season === 'winter' ? '#ffffff' : '#ff4f5e'} />
		))}
		{season === 'winter' ? <path d="M40 92 Q130 0 220 92 Q130 60 40 92 Z" fill="#ffffff" /> : null}
	</svg>
	);
};

const PineTree: React.FC<{x: number; y: number; s: number; color: string}> = ({x, y, s, color}) => {
	const {season} = React.useContext(Look);
	return (
		<svg style={{position: 'absolute', left: x - 90 * s, top: y - 300 * s}} width={180 * s} height={300 * s} viewBox="0 0 180 300">
			<rect x={80} y={240} width={20} height={60} fill="#6e4424" />
			<path d="M90 0 L150 110 L120 110 L170 190 L130 190 L180 260 L0 260 L50 190 L10 190 L60 110 L30 110 Z" fill={color} />
			{season === 'winter' ? <path d="M90 0 L118 52 L90 40 L62 52 Z M60 110 L120 110 L104 130 L76 130 Z" fill="#ffffff" /> : null}
		</svg>
	);
};

const Bush: React.FC<{x: number; y: number; s: number; color?: string}> = ({x, y, s, color: given = '#4cb944'}) => {
	const {season} = React.useContext(Look);
	const color = season === 'spring' ? given : LEAVES[season][(Math.round(x) + 1) % 3];
	return (
	<svg style={{position: 'absolute', left: x - 90 * s, top: y - 80 * s}} width={180 * s} height={80 * s} viewBox="0 0 180 80">
		<circle cx={50} cy={50} r={36} fill={mix(color, '#000000', 0.1)} />
		<circle cx={130} cy={50} r={36} fill={mix(color, '#000000', 0.1)} />
		<circle cx={90} cy={40} r={40} fill={color} />
		<rect x={20} y={50} width={140} height={30} rx={15} fill={color} />
		<circle cx={76} cy={26} r={10} fill="#fff" opacity={0.18} />
		{season === 'winter' ? <ellipse cx={90} cy={14} rx={46} ry={12} fill="#ffffff" /> : null}
	</svg>
	);
};

const Mushroom: React.FC<{x: number; y: number}> = ({x, y}) => (
	<svg style={{position: 'absolute', left: x - 40, top: y - 70}} width={80} height={70} viewBox="0 0 80 70">
		<rect x={30} y={34} width={20} height={36} rx={8} fill="#fff3e0" />
		<path d="M4 40 Q40 -10 76 40 Z" fill="#ff4f5e" />
		{[
			[24, 26],
			[46, 16],
			[58, 32],
		].map(([cx, cy]) => (
			<circle key={cx} cx={cx} cy={cy} r={5} fill="#fff" />
		))}
	</svg>
);

const Barn: React.FC = () => (
	<svg style={{position: 'absolute', left: 50, top: 420}} width={600} height={470} viewBox="0 0 600 470">
		<rect x={440} y={110} width={110} height={360} fill="#cfd8e3" />
		<path d="M440 110 Q495 40 550 110 Z" fill="#9aa8b8" />
		{[170, 230, 290, 350, 410].map((y) => (
			<line key={y} x1={440} y1={y} x2={550} y2={y} stroke="#b4c0cf" strokeWidth={4} />
		))}
		<path d="M10 175 L215 40 L420 175 Z" fill="#8f2a26" />
		<rect x={40} y={165} width={350} height={305} fill="#d9443c" />
		{[200, 240, 280, 320, 360, 400, 440].map((y) => (
			<line key={y} x1={40} y1={y} x2={390} y2={y} stroke="#c23a33" strokeWidth={3} />
		))}
		<path d="M10 175 L215 40 L420 175" fill="none" stroke="#fff" strokeWidth={18} strokeLinejoin="round" />
		<rect x={150} y={290} width={130} height={180} fill="#fff" />
		<rect x={162} y={302} width={106} height={168} fill="#a8322d" />
		<path d="M162 302 L268 470 M268 302 L162 470" stroke="#fff" strokeWidth={10} />
		<rect x={175} y={110} width={80} height={70} fill="#fff" />
		<rect x={184} y={119} width={62} height={52} fill="#5a3a22" />
		<path d="M184 145 L246 145" stroke="#f0c75e" strokeWidth={8} />
		<rect x={60} y={230} width={56} height={46} fill="#fff" />
		<rect x={66} y={236} width={44} height={34} fill="#7fc4ff" />
		<rect x={314} y={230} width={56} height={46} fill="#fff" />
		<rect x={320} y={236} width={44} height={34} fill="#7fc4ff" />
	</svg>
);

const HayBale: React.FC<{x: number; y: number}> = ({x, y}) => (
	<svg style={{position: 'absolute', left: x - 60, top: y - 90}} width={120} height={90} viewBox="0 0 120 90">
		<rect x={4} y={10} width={112} height={80} rx={18} fill="#f2c94c" />
		<circle cx={36} cy={50} r={26} fill="#e6b437" />
		<path d="M36 50 m-16 0 a16 16 0 1 0 32 0 a10 10 0 1 0 -20 0" fill="none" stroke="#c9952a" strokeWidth={4} />
		<path d="M76 20 L76 86 M96 20 L96 86" stroke="#d9a83a" strokeWidth={4} />
	</svg>
);

const Fence: React.FC<{from: number; to: number; y: number}> = ({from, to, y}) => (
	<svg style={{position: 'absolute', left: from, top: y}} width={to - from} height={120} viewBox={`0 0 ${to - from} 120`}>
		<rect x={0} y={30} width={to - from} height={14} fill="#f1d9b5" />
		<rect x={0} y={70} width={to - from} height={14} fill="#f1d9b5" />
		{Array.from({length: Math.floor((to - from) / 70) + 1}, (_, i) => (
			<path key={i} d={`M${i * 70 + 4} 120 V12 L${i * 70 + 17} 0 L${i * 70 + 30} 12 V120 Z`} fill="#fbe8c8" stroke="#e0c49a" strokeWidth={3} />
		))}
	</svg>
);

const Rain: React.FC<{frame: number}> = ({frame}) => (
	<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
		{Array.from({length: 110}, (_, i) => {
			const x = hash(i + 7) * 2000 - 40;
			const speed = 26 + hash(i + 3) * 14;
			const y = ((hash(i + 11) * 1200 + frame * speed) % 1200) - 100;
			return <path key={i} d={`M${x} ${y} l-10 34`} stroke="#e4f2ff" strokeWidth={4} strokeLinecap="round" opacity={0.7} />;
		})}
		{[
			[300, 1010],
			[760, 1040],
			[1240, 1020],
			[1650, 1035],
		].map(([x, y], i) => {
			const p = ((frame + i * 13) % 40) / 40;
			return (
				<g key={i}>
					<ellipse cx={x} cy={y} rx={110} ry={20} fill="#8fb6dd" opacity={0.8} />
					<ellipse cx={x} cy={y} rx={20 + p * 80} ry={4 + p * 14} fill="none" stroke="#e4f2ff" strokeWidth={3} opacity={1 - p} />
				</g>
			);
		})}
	</svg>
);

const Fireflies: React.FC<{frame: number}> = ({frame}) => (
	<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
		<defs>
			<radialGradient id="firefly">
				<stop offset="0%" stopColor="#fbff9a" />
				<stop offset="100%" stopColor="#fbff9a" stopOpacity={0} />
			</radialGradient>
		</defs>
		{Array.from({length: 16}, (_, i) => {
			const x = hash(i + 21) * 1920 + Math.sin(frame / 50 + i) * 60;
			const y = 760 + hash(i + 31) * 260 + Math.cos(frame / 40 + i * 2) * 30;
			const glow = 0.3 + 0.7 * Math.max(0, Math.sin(frame / 20 + i * 1.7));
			return <circle key={i} cx={x} cy={y} r={16} fill="url(#firefly)" opacity={glow} />;
		})}
	</svg>
);

const ShootingStar: React.FC<{frame: number}> = ({frame}) => {
	const p = (frame % 300) / 40;
	if (p > 1) return null;
	const x = 300 + p * 700;
	const y = 80 + p * 260;
	return (
		<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
			<path d={`M${x} ${y} L${x - 160} ${y - 60}`} stroke="#fff8c8" strokeWidth={5} strokeLinecap="round" opacity={1 - p} />
			<circle cx={x} cy={y} r={7} fill="#fff" opacity={1 - p} />
		</svg>
	);
};

const DiscoBall: React.FC<{frame: number}> = ({frame}) => (
	<svg style={{position: 'absolute', left: 860, top: -20}} width={200} height={240} viewBox="0 0 200 240">
		<line x1={100} y1={0} x2={100} y2={50} stroke="#c9c9d9" strokeWidth={4} />
		<clipPath id="ball-clip">
			<circle cx={100} cy={130} r={80} />
		</clipPath>
		<circle cx={100} cy={130} r={80} fill="#8f9bb3" />
		<g clipPath="url(#ball-clip)">
			{Array.from({length: 10}, (_, row) =>
				Array.from({length: 12}, (_, col) => {
					const x = 20 + col * 16 - ((frame * 0.8) % 16);
					const y = 50 + row * 16;
					const lit = hash(row * 12 + col + Math.floor(frame / 6)) > 0.7;
					return <rect key={`${row}-${col}`} x={x} y={y} width={14} height={14} fill={lit ? '#ffffff' : hash(row + col * 7) > 0.5 ? '#c7d0e0' : '#9aa6bd'} />;
				}),
			)}
		</g>
		<circle cx={74} cy={104} r={22} fill="#fff" opacity={0.35} />
	</svg>
);

/** The whole-screen backdrop for a scene. */
export const Scenery: React.FC<{bg: Bg; tint: string | null}> = ({bg, tint}) => {
	const frame = useCurrentFrame();
	if (bg === 'night') {
		return (
			<AbsoluteFill style={{background: 'linear-gradient(#0a1238 0%, #1c2a66 60%, #34468a 100%)'}}>
				<Stars count={80} frame={frame} />
				<ShootingStar frame={frame} />
				<svg style={{position: 'absolute', left: 1450, top: -60}} width={500} height={500} viewBox="0 0 500 500">
					<defs>
						<radialGradient id="moon-glow">
							<stop offset="30%" stopColor="#fff6c4" stopOpacity={0.55} />
							<stop offset="100%" stopColor="#fff6c4" stopOpacity={0} />
						</radialGradient>
					</defs>
					<circle cx={250} cy={250} r={240} fill="url(#moon-glow)" />
				</svg>
				<div style={{position: 'absolute', right: 160, top: 70}}>
					<Icon name="moon" color="#ffe58a" size={240} blink={0.08} />
				</div>
				<Land c={NIGHT_LAND} />
				<Fireflies frame={frame} />
			</AbsoluteFill>
		);
	}
	if (bg === 'dusk') {
		return (
			<AbsoluteFill style={{background: 'linear-gradient(#ff7f5c 0%, #ffad7a 40%, #ffd9a0 75%, #ffe9c2 100%)'}}>
				<svg style={{position: 'absolute', left: 660, top: 420}} width={600} height={600} viewBox="0 0 600 600">
					<defs>
						<radialGradient id="dusk-sun">
							<stop offset="30%" stopColor="#fff2a0" stopOpacity={0.9} />
							<stop offset="100%" stopColor="#ffd060" stopOpacity={0} />
						</radialGradient>
					</defs>
					<circle cx={300} cy={300} r={300} fill="url(#dusk-sun)" />
					<circle cx={300} cy={300} r={120} fill="#ffcf3f" />
				</svg>
				{[0, 1, 2].map((i) => (
					<Cloud key={i} x={((i * 700 + frame * 0.4) % 2300) - 300} y={90 + i * 70} s={0.8 - i * 0.12} color="#ffc6b0" shade="#f2a08c" />
				))}
				<Birds frame={frame} color="#7a3b3b" />
				<Land c={DUSK_LAND} />
			</AbsoluteFill>
		);
	}
	if (bg === 'rain') {
		return (
			<AbsoluteFill style={{background: 'linear-gradient(#7d91ab 0%, #a9bbcf 65%, #c9d6e3 100%)'}}>
				{[0, 1, 2, 3, 4].map((i) => (
					<Cloud key={i} x={((i * 470 + frame * 0.7) % 2300) - 300} y={20 + (i % 2) * 90} s={1.4 - (i % 2) * 0.35} color="#8e9cb2" shade="#6f7d93" />
				))}
				<Land c={RAIN_LAND} />
				<Rain frame={frame} />
			</AbsoluteFill>
		);
	}
	if (bg === 'party') {
		return (
			<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 35%, #34197a 0%, #170b3d 55%, #0b0620 100%)'}}>
				<Stars count={50} frame={frame} maxY={760} />
				{Array.from({length: 14}, (_, i) => {
					const a = frame / 50 + i * 0.9;
					return (
						<div
							key={i}
							style={{
								position: 'absolute',
								left: 960 + Math.cos(a) * (300 + (i % 4) * 180) - 14,
								top: 380 + Math.sin(a * 1.3) * (150 + (i % 3) * 90) - 14,
								width: 28,
								height: 28,
								borderRadius: '50%',
								background: RAINBOW[i % 7],
								opacity: 0.5,
								filter: 'blur(4px)',
							}}
						/>
					);
				})}
				<DiscoBall frame={frame} />
			</AbsoluteFill>
		);
	}
	const tintLayer = tint ? <AbsoluteFill style={{background: `radial-gradient(circle at 50% 55%, ${mix(tint, '#ffffff', 0.35)} 0%, transparent 55%)`, opacity: 0.5}} /> : null;
	if (bg === 'beach') {
		return (
			<AbsoluteFill style={{background: 'linear-gradient(#4ab4ff 0%, #bfe9ff 60%, #fff6dc 100%)'}}>
				{[0, 1, 2].map((i) => (
					<Cloud key={i} x={((i * 700 + frame * 0.5) % 2300) - 300} y={70 + i * 60} s={0.9 - i * 0.15} />
				))}
				<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
					<defs>
						<linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
							<stop offset="0%" stopColor="#3fb7e8" />
							<stop offset="100%" stopColor="#1f8fd0" />
						</linearGradient>
					</defs>
					<circle cx={1650} cy={170} r={80} fill="#ffd23f" />
					<rect y={600} width={1920} height={240} fill="url(#sea)" />
					{[0, 1, 2, 3].map((k) => (
						<path key={k} d={`M${-200 + ((frame * (1 + k * 0.3) + k * 300) % 400)} ${640 + k * 45} q50 -16 100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0 t100 0`} fill="none" stroke="#ffffff" strokeWidth={4} opacity={0.5} />
					))}
					<g transform={`translate(${300 + Math.sin(frame / 60) * 20} 590)`}>
						<path d="M-50 0 L50 0 L36 18 L-36 18 Z" fill="#ff6b4a" />
						<path d="M0 0 L0 -90 L44 -6 Z" fill="#ffffff" />
					</g>
					<path d={`M0 790 Q480 ${760 + Math.sin(frame / 20) * 8} 960 785 T1920 780 L1920 1080 L0 1080 Z`} fill="#e8c784" />
					<path d="M0 820 Q480 800 960 818 T1920 812 L1920 1080 L0 1080 Z" fill="#f6dca0" />
					<g transform="translate(1620 900)">
						<rect x={-6} y={-330} width={12} height={330} fill="#8a6a4a" />
						<path d="M-200 -300 Q0 -420 200 -300 Z" fill="#ff4f5e" />
						<path d="M-120 -335 Q-60 -395 0 -405 L0 -300 Z M60 -390 Q120 -360 200 -300 L120 -300 Z" fill="#ffffff" />
						<rect x={-230} y={-10} width={200} height={40} rx={8} fill="#2f8cff" transform="rotate(-6)" />
					</g>
					<g transform="translate(300 980)">
						<path d="M-30 -60 L30 -60 L22 0 L-22 0 Z" fill="#ffc92e" />
						<path d="M-30 -60 Q0 -100 30 -60" stroke="#ff8a1f" strokeWidth={6} fill="none" />
					</g>
					{[
						[560, 1000, '#ff8a6a'],
						[1200, 1030, '#ffb0d0'],
						[900, 1050, '#ffd27a'],
					].map(([x, y, c], i) => (
						<path key={i} d={`M${x} ${(y as number) - 22} L${(x as number) + 7} ${(y as number) - 7} L${(x as number) + 22} ${(y as number) - 5} L${(x as number) + 10} ${(y as number) + 5} L${(x as number) + 14} ${(y as number) + 20} L${x} ${(y as number) + 11} L${(x as number) - 14} ${(y as number) + 20} L${(x as number) - 10} ${(y as number) + 5} L${(x as number) - 22} ${(y as number) - 5} L${(x as number) - 7} ${(y as number) - 7} Z`} fill={c as string} />
					))}
				</svg>
				<Birds frame={frame} color="#ffffff" />
				{tintLayer}
			</AbsoluteFill>
		);
	}
	if (bg === 'underwater') {
		return (
			<AbsoluteFill style={{background: 'linear-gradient(#5fd0f0 0%, #2a9ad8 55%, #1c6fb0 100%)'}}>
				<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
					{[0, 1, 2, 3, 4].map((k) => (
						<path key={k} d={`M${200 + k * 380 + Math.sin(frame / 40 + k) * 40} 0 L${300 + k * 380} 0 L${420 + k * 380 + Math.sin(frame / 40 + k) * 60} 1080 L${260 + k * 380} 1080 Z`} fill="#ffffff" opacity={0.07} />
					))}
					<path d="M0 900 Q480 870 960 895 T1920 890 L1920 1080 L0 1080 Z" fill="#f0d9a0" />
					{[120, 300, 1500, 1700, 1850].map((x, i) => (
						<path key={x} d={`M${x} 960 Q${x + Math.sin(frame / 18 + i) * 30} 860 ${x + Math.sin(frame / 22 + i) * 20} ${740 - (i % 2) * 60} Q${x + 30 + Math.sin(frame / 15 + i) * 30} 860 ${x + 20} 960 Z`} fill={i % 2 ? '#3cc75a' : '#2f9e44'} />
					))}
					{[
						[480, 930, '#ff6fb5'],
						[1300, 940, '#ff8a1f'],
					].map(([x, y, c]) => (
						<g key={x as number} fill={c as string}>
							<circle cx={x as number} cy={y as number} r={34} />
							<circle cx={(x as number) - 30} cy={(y as number) - 30} r={22} />
							<circle cx={(x as number) + 28} cy={(y as number) - 34} r={20} />
						</g>
					))}
					{Array.from({length: 4}, (_, i) => {
						const dir = i % 2 ? -1 : 1;
						const x = ((i * 520 + frame * (2 + i * 0.6) * dir) % 2300 + 2300) % 2300 - 200;
						const y = 220 + i * 140 + Math.sin(frame / 20 + i) * 20;
						const c = ['#ffc92e', '#ff6b4a', '#9b5cff', '#ff6fb5'][i];
						return (
							<g key={i} transform={`translate(${x} ${y}) scale(${dir} 1)`}>
								<ellipse cx={0} cy={0} rx={40} ry={24} fill={c} />
								<path d={`M-36 0 L-66 ${-20 + Math.sin(frame / 4 + i) * 6} L-66 ${20 + Math.sin(frame / 4 + i) * 6} Z`} fill={c} />
								<circle cx={18} cy={-6} r={6} fill="#ffffff" />
								<circle cx={20} cy={-6} r={3} fill="#2b2b3a" />
							</g>
						);
					})}
					{Array.from({length: 14}, (_, i) => {
						const p = ((frame * (1 + (i % 4) * 0.4) + i * 90) % 1100) / 1100;
						return <circle key={`b${i}`} cx={100 + i * 135 + Math.sin(frame / 15 + i) * 12} cy={1050 - p * 1150} r={6 + (i % 3) * 4} fill="none" stroke="#ffffff" strokeWidth={3} opacity={0.6} />;
					})}
				</svg>
				{tintLayer}
			</AbsoluteFill>
		);
	}
	if (bg === 'bedroom') {
		return (
			<AbsoluteFill style={{background: '#ffe7d6'}}>
				<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
					{Array.from({length: 60}, (_, i) => (
						<circle key={i} cx={(i % 12) * 170 + 60 + (Math.floor(i / 12) % 2) * 85} cy={Math.floor(i / 12) * 150 + 60} r={8} fill="#ffcfb3" />
					))}
					<rect y={820} width={1920} height={260} fill="#d9a873" />
					{Array.from({length: 8}, (_, i) => (
						<line key={i} x1={i * 260} y1={820} x2={i * 260 - 80} y2={1080} stroke="#c4925e" strokeWidth={4} />
					))}
					<rect x={760} y={150} width={400} height={360} rx={20} fill="#1c2a5e" />
					<circle cx={1060} cy={240} r={44} fill="#fff6c4" />
					<circle cx={1078} cy={228} r={40} fill="#1c2a5e" />
					{Array.from({length: 9}, (_, i) => (
						<circle key={i} cx={790 + ((i * 97) % 340)} cy={180 + ((i * 61) % 300)} r={3 + (i % 3)} fill="#fff6c4" opacity={0.5 + 0.5 * Math.abs(Math.sin(frame / 20 + i))} />
					))}
					<rect x={760} y={150} width={400} height={360} rx={20} fill="none" stroke="#ffffff" strokeWidth={14} />
					<path d="M720 130 Q760 330 730 540 L800 540 Q780 330 800 130 Z" fill="#9b5cff" />
					<path d="M1200 130 Q1160 330 1190 540 L1120 540 Q1140 330 1120 130 Z" fill="#9b5cff" />
					<ellipse cx={960} cy={960} rx={420} ry={70} fill="#ff9fc4" opacity={0.8} />
					<g transform="translate(1260 560)">
						<rect x={0} y={0} width={70} height={340} rx={20} fill="#c9875a" />
						<rect x={0} y={170} width={600} height={140} rx={30} fill="#2f8cff" />
						{Array.from({length: 6}, (_, i) => (
							<path key={i} d={`M${100 + i * 80} 220 l8 16 l18 2 l-13 12 l4 18 l-17 -9 l-17 9 l4 -18 l-13 -12 l18 -2 Z`} fill="#ffd23f" />
						))}
						<rect x={60} y={130} width={160} height={60} rx={28} fill="#ffffff" />
					</g>
					<g transform="translate(260 640)">
						<rect x={0} y={0} width={220} height={260} fill="#c9875a" />
						{[0, 1, 2].map((r) => (
							<g key={r}>
								<rect x={10} y={20 + r * 84} width={200} height={10} fill="#a86c44" />
								{[0, 1, 2, 3, 4].map((k) => (
									<rect key={k} x={20 + k * 36} y={r * 84 - 40 + 20} width={26} height={58} fill={RAINBOW[(r * 5 + k) % 7]} />
								))}
							</g>
						))}
					</g>
					{[
						[560, 960, '#ff3b3b'],
						[620, 960, '#2f8cff'],
						[590, 910, '#ffc92e'],
					].map(([x, y, c], i) => (
						<rect key={i} x={x as number} y={y as number} width={50} height={50} rx={8} fill={c as string} />
					))}
					<circle cx={1880} cy={560} r={220} fill="#fff2b0" opacity={0.25} />
				</svg>
				{tintLayer}
			</AbsoluteFill>
		);
	}
	return (
		<AbsoluteFill>
			<Background tint={tint} />
			{bg === 'farm' ? (
				<>
					<Barn />
					<Fence from={680} to={1920} y={790} />
					<HayBale x={1500} y={930} />
					<HayBale x={1660} y={950} />
				</>
			) : null}
			{bg === 'forest' ? (
				<>
					{[60, 260, 420, 600, 1320, 1480, 1640, 1830].map((x, i) => (
						<PineTree key={x} x={x} y={860 + (i % 2) * 20} s={1 + (i % 3) * 0.15} color={i % 2 ? '#2f8f45' : '#3a9e50'} />
					))}
					<Tree x={140} y={900} s={1.5} />
					<Tree x={1790} y={910} s={1.6} />
					<Tree x={1500} y={880} s={1.1} color="#36a04a" />
					<Bush x={420} y={930} s={1.2} />
					<Mushroom x={620} y={960} />
					<Mushroom x={1330} y={975} />
					{Array.from({length: 6}, (_, i) => {
						const t = (frame + i * 60) % 360;
						const x = 200 + i * 300 + Math.sin(t / 25) * 60;
						const y = -40 + t * 3;
						return (
							<svg key={i} style={{position: 'absolute', left: x, top: y}} width={40} height={30} viewBox="0 0 40 30">
								<path d="M2 15 Q20 -5 38 15 Q20 35 2 15Z" fill={['#ffb02e', '#ff7a3d', '#9ccc3d'][i % 3]} transform={`rotate(${t * 2} 20 15)`} />
							</svg>
						);
					})}
				</>
			) : null}
			{bg === 'garden' ? (
				<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
					{Array.from({length: 26}, (_, i) => (
						<g key={i}>
							<rect x={i * 76} y={720} width={16} height={130} fill="#ffffff" />
							<path d={`M${i * 76} 720 l8 -16 l8 16 Z`} fill="#ffffff" />
						</g>
					))}
					<rect y={760} width={1920} height={12} fill="#ffffff" />
					<rect y={800} width={1920} height={12} fill="#ffffff" />
					{Array.from({length: 11}, (_, i) => (
						<g key={`c${i}`} transform={`translate(${120 + i * 165} 868)`}>
							<path d="M0 0 L-8 -40 M0 0 L0 -46 M0 0 L8 -40" stroke="#3cc75a" strokeWidth={8} strokeLinecap="round" />
							<path d="M-8 0 L8 0 L0 26 Z" fill="#ff8a1f" />
						</g>
					))}
					<g transform="translate(1760 900)">
						<path d="M-50 -60 L40 -60 L50 0 L-60 0 Z" fill="#2f8cff" />
						<path d="M40 -50 L100 -90" stroke="#2f8cff" strokeWidth={12} strokeLinecap="round" />
					</g>
				</svg>
			) : null}
			{bg === 'playground' ? (
				<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
					<g transform="translate(180 880)">
						<rect x={0} y={-360} width={14} height={360} fill="#ff3b3b" />
						<rect x={80} y={-360} width={14} height={360} fill="#ff3b3b" />
						{Array.from({length: 7}, (_, k) => (
							<rect key={k} x={0} y={-50 - k * 46} width={94} height={8} fill="#ff3b3b" />
						))}
						<rect x={-10} y={-372} width={114} height={20} fill="#ffc92e" />
						<path d="M94 -360 Q260 -260 380 -20 L410 -20 Q290 -280 104 -380 Z" fill="#2f8cff" />
					</g>
					<g transform="translate(1340 880)">
						<path d="M0 0 L60 -380 L120 0 M420 0 L480 -380 L540 0" stroke="#9b5cff" strokeWidth={16} fill="none" />
						<rect x={50} y={-392} width={440} height={18} fill="#9b5cff" />
						{[180, 360].map((x, k) => {
							const a = Math.sin(frame / 18 + k * 2) * 18;
							return (
								<g key={x} transform={`rotate(${a} ${x} -380)`}>
									<line x1={x - 30} y1={-380} x2={x - 30} y2={-140} stroke="#5a4a3a" strokeWidth={5} />
									<line x1={x + 30} y1={-380} x2={x + 30} y2={-140} stroke="#5a4a3a" strokeWidth={5} />
									<rect x={x - 44} y={-146} width={88} height={16} rx={6} fill="#ff8a1f" />
								</g>
							);
						})}
					</g>
				</svg>
			) : null}
			{bg === 'park' ? (
				<>
					<svg style={{position: 'absolute', left: 0, top: 860}} width={1920} height={220} viewBox="0 0 1920 220">
						<path d="M760 220 Q900 120 1040 70 Q1180 20 1300 0 L1360 0 Q1240 30 1110 80 Q980 130 900 220 Z" fill="#f3dfb5" opacity={0.9} />
					</svg>
					<Tree x={170} y={900} s={1.3} />
					<Tree x={1760} y={890} s={1.2} color="#36a04a" />
					<Bush x={420} y={920} s={0.9} color="#5cc24b" />
					<Bush x={1520} y={915} s={1} color="#4cb944" />
				</>
			) : null}
			{bg === 'pond' ? (
				<>
					<svg style={{position: 'absolute', left: 960, top: 860}} width={900} height={220} viewBox="0 0 900 220">
						<defs>
							<linearGradient id="pond-water" x1="0" y1="0" x2="0" y2="1">
								<stop offset="0%" stopColor="#8fdcff" />
								<stop offset="100%" stopColor="#3fa6e8" />
							</linearGradient>
						</defs>
						<ellipse cx={450} cy={110} rx={440} ry={100} fill="#3a8fd0" />
						<ellipse cx={450} cy={104} rx={410} ry={84} fill="url(#pond-water)" />
						{[0, 1, 2].map((k) => {
							const p = ((frame + k * 30) % 90) / 90;
							return <ellipse key={k} cx={300 + k * 160} cy={100} rx={20 + p * 90} ry={6 + p * 22} fill="none" stroke="#fff" strokeWidth={3} opacity={(1 - p) * 0.7} />;
						})}
						{[
							[180, 110],
							[560, 80],
							[700, 130],
						].map(([x, y]) => (
							<g key={x}>
								<ellipse cx={x} cy={y} rx={48} ry={18} fill="#3cc75a" />
								<path d={`M${x} ${y} l44 -10 l0 14 Z`} fill="#6fc6f5" />
							</g>
						))}
						<g transform="translate(560 66)">
							{[-30, 0, 30].map((r) => (
								<ellipse key={r} cx={0} cy={-8} rx={8} ry={16} fill="#ff8fc6" transform={`rotate(${r})`} />
							))}
							<circle r={5} fill="#ffd23f" />
						</g>
						{[40, 70, 830, 860].map((x, i) => (
							<g key={x}>
								<path d={`M${x} 140 Q${x + 6} 60 ${x + (i % 2 ? 10 : -6)} 20`} stroke="#4f9a3a" strokeWidth={6} fill="none" />
								<rect x={x - 6 + (i % 2 ? 8 : -6)} y={10} width={12} height={34} rx={6} fill="#8a5a33" />
							</g>
						))}
					</svg>
				</>
			) : null}
		</AbsoluteFill>
	);
};

export const Confetti: React.FC<{x: number; y: number; at: number; count?: number; spread?: number}> = ({x, y, at, count = 36, spread = 1}) => {
	const frame = useCurrentFrame();
	const t = frame - at;
	if (t < 0 || t > 70) return null;
	return (
		<svg style={{position: 'absolute', inset: 0, overflow: 'visible'}} width={1920} height={1080}>
			{Array.from({length: count}, (_, i) => {
				const a = hash(i + at) * Math.PI * 2;
				const v = (10 + hash(i * 3 + at) * 16) * spread;
				const px = x + Math.cos(a) * v * t;
				const py = y + Math.sin(a) * v * t * 0.8 + 0.35 * t * t;
				const c = RAINBOW[i % RAINBOW.length];
				const o = clamp(1 - (t - 40) / 30);
				return i % 2 ? (
					<circle key={i} cx={px} cy={py} r={9} fill={c} opacity={o} />
				) : (
					<rect key={i} x={px - 8} y={py - 5} width={16} height={10} fill={c} opacity={o} transform={`rotate(${t * 9 + i * 40} ${px} ${py})`} />
				);
			})}
		</svg>
	);
};

const Zzz: React.FC<{x: number; y: number; frame: number}> = ({x, y, frame}) => (
	<>
		{[0, 1, 2].map((k) => {
			const p = ((frame + k * 20) % 60) / 60;
			return (
				<div key={k} style={{position: 'absolute', left: x + p * 60 + k * 10, top: y - p * 120, opacity: 1 - p}}>
					<span style={textStyle('#8f7dff', 50 + k * 10)}>z</span>
				</div>
			);
		})}
	</>
);

const posAt = (keys: Key[], f: number) => {
	if (f <= keys[0].t) return {x: keys[0].x, y: keys[0].y, moving: false};
	for (let i = 0; i < keys.length - 1; i++) {
		const a = keys[i];
		const b = keys[i + 1];
		if (f < b.t) {
			const p = (f - a.t) / Math.max(1, b.t - a.t);
			const e = p * p * (3 - 2 * p);
			return {x: a.x + (b.x - a.x) * e, y: a.y + (b.y - a.y) * e, moving: a.x !== b.x || a.y !== b.y};
		}
	}
	const last = keys[keys.length - 1];
	return {x: last.x, y: last.y, moving: false};
};

/** Where and how an actor is drawn on frame f: walking, breathing, squash and stretch, acted moves, lip-sync. */
const actorPose = (actor: Actor, f: number, idx: number) => {
	const base = posAt(actor.keys, f);
	const s = actor.size / 420;
	let {x, y} = base;
	let rot = 0;
	let sx = 1;
	let sy = 1;
	let walk: number | undefined;
	const airborne = actor.fly && (base.moving || base.y < 880);
	let arms: Pose['arms'] = airborne ? 'flap' : 'down';
	if (base.moving && !actor.fly) {
		walk = (f * Math.PI) / 8;
		y -= Math.abs(Math.sin(walk)) * 16 * s;
		rot = Math.sin(walk) * 3;
		arms = 'swing';
	} else if (airborne) {
		y += Math.sin(f / (base.moving ? 4 : 10)) * 12;
		rot = base.moving ? Math.sin(f / 5) * 5 : 0;
	} else {
		sy = 1 + Math.sin((f + idx * 23) / 16) * 0.018;
		sx = 2 - sy;
	}
	let sleeping = false;
	for (const a of actor.acts) {
		const d = f - a.t;
		if (d < 0) continue;
		if (a.kind === 'sleep') sleeping = true;
		if (a.kind === 'wake') sleeping = false;
		if (a.kind === 'jump' && d < 30) {
			if (d < 5) {
				sy *= 1 - 0.13 * Math.sin((Math.PI * d) / 5);
				sx *= 1 + 0.1 * Math.sin((Math.PI * d) / 5);
			} else if (d < 25) {
				y -= Math.sin((Math.PI * (d - 5)) / 20) * 160 * s;
				sy *= 1.07;
				sx *= 0.95;
				arms = 'up';
			} else {
				sy *= 1 - 0.13 * Math.sin((Math.PI * (d - 25)) / 5);
				sx *= 1 + 0.1 * Math.sin((Math.PI * (d - 25)) / 5);
			}
		}
		if (a.kind === 'shake' && d < 26) {
			x += Math.sin(d * 1.3) * 18 * (1 - d / 26);
			rot += Math.sin(d * 1.3) * 6 * (1 - d / 26);
		}
		if (a.kind === 'spin' && d < 24) {
			rot += (360 * d) / 24;
			arms = 'up';
		}
		if (a.kind === 'wave' && d < 54) arms = 'wave';
	}
	if (sleeping) {
		arms = 'down';
		sy = 1 + Math.sin(f / 22) * 0.03;
		sx = 2 - sy;
	}
	let talk = 0;
	for (const t of actor.talk ?? []) {
		const k = f - t.at;
		if (k >= 0 && k < t.m.length) {
			talk = Number(t.m[k]) / 9;
			break;
		}
	}
	return {x, y, rot, sx, sy, sleeping, walk, arms, talk, feetY: base.y};
};

/** Frames when an actor kicks up dust: starting or stopping a walk, landing a jump. */
const dustFrames = (actor: Actor) => {
	if (actor.fly) return [];
	const out: number[] = [];
	const k = actor.keys;
	for (let i = 0; i < k.length - 1; i++) {
		const moving = k[i].x !== k[i + 1].x || k[i].y !== k[i + 1].y;
		const before = i > 0 && (k[i - 1].x !== k[i].x || k[i - 1].y !== k[i].y);
		const after = i + 2 < k.length && (k[i + 1].x !== k[i + 2].x || k[i + 1].y !== k[i + 2].y);
		if (moving && !before) out.push(k[i].t);
		if (moving && !after) out.push(k[i + 1].t);
	}
	for (const a of actor.acts) if (a.kind === 'jump') out.push(a.t + 25);
	return out;
};

const Dust: React.FC<{x: number; y: number; d: number}> = ({x, y, d}) => {
	const p = d / 18;
	return (
		<svg style={{position: 'absolute', inset: 0, overflow: 'visible'}} width={1920} height={1080}>
			{[-1, -0.4, 0.4, 1].map((k) => (
				<circle key={k} cx={x + k * (40 + p * 70)} cy={y - 8 - p * 22 * (1 - Math.abs(k) * 0.4)} r={12 + p * 18} fill="#ffffff" opacity={(1 - p) * 0.75} />
			))}
		</svg>
	);
};

/** Slowly turning sunburst. */
export const Rays: React.FC<{x: number; y: number; r: number; color: string; opacity: number; frame: number; count?: number}> = ({
	x,
	y,
	r,
	color,
	opacity,
	frame,
	count = 14,
}) => (
	<svg style={{position: 'absolute', left: x - r, top: y - r, overflow: 'visible'}} width={r * 2} height={r * 2} viewBox={`${-r} ${-r} ${r * 2} ${r * 2}`}>
		<defs>
			<radialGradient id={`rays-${Math.round(x)}-${Math.round(y)}`}>
				<stop offset="0%" stopColor={color} stopOpacity={1} />
				<stop offset="100%" stopColor={color} stopOpacity={0} />
			</radialGradient>
		</defs>
		<g transform={`rotate(${frame * 0.6})`} opacity={opacity}>
			{Array.from({length: count}, (_, i) => {
				const a0 = (i / count) * Math.PI * 2;
				const a1 = a0 + Math.PI / count;
				return <path key={i} d={`M0 0 L${Math.cos(a0) * r} ${Math.sin(a0) * r} L${Math.cos(a1) * r} ${Math.sin(a1) * r} Z`} fill={`url(#rays-${Math.round(x)}-${Math.round(y)})`} />;
			})}
		</g>
	</svg>
);

// ---------------------------------------------------------------- scenes
export const TitleCard: React.FC<{scene: Extract<FunScene, {type: 'title'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const n = scene.heroes.length;
	const out = scene.duration - 14;
	const feet = scene.title.length > 1 ? 1010 : 960;
	return (
		<AbsoluteFill>
			<Rays x={960} y={360} r={900} color={scene.rays ?? '#ffffff'} opacity={scene.rays ? 0.4 : 0.28} frame={frame} count={16} />
			<Pop at={0} outAt={out} bob={4}>
				<div style={{position: 'absolute', top: 80, width: '100%'}}>
					<PopWord text={scene.top} color={scene.topColor ?? '#2F8CFF'} size={84} startFrame={2} />
				</div>
				{scene.title.map((line, i) => (
					<div key={line} style={{position: 'absolute', top: 210 + i * 170, width: '100%'}}>
						<PopWord text={line} color={RAINBOW} size={line.length > 14 ? 130 : 160} startFrame={10 + i * 14} />
					</div>
				))}
			</Pop>
			{scene.heroes.map((h, i) => {
				const x = 960 + (i - (n - 1) / 2) * (h.body ? 290 : 270);
				return (
					<Pop key={i} at={20 + i * 5} outAt={out} seed={i} bob={h.body ? 4 : 10}>
						{h.body ? (
							<Character hero={h} x={x} feetY={feet} height={360} pose={{blink: blinkAt(frame, i), arms: i % 2 ? 'up' : 'wave', frame: frame + i * 9}} />
						) : (
							<HeroView hero={h} x={x} y={scene.title.length > 1 ? 820 : 720} size={230} blink={blinkAt(frame, i)} />
						)}
					</Pop>
				);
			})}
		</AbsoluteFill>
	);
};

export const StoryScene: React.FC<{scene: Extract<FunScene, {type: 'story'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const poses = scene.actors.map((a, i) => actorPose(a, frame, i));
	const visible = (a: {from?: number; until?: number}) => (a.from === undefined || frame >= a.from) && (a.until === undefined || frame < a.until);
	const iris = Math.min(clamp(frame / 12), clamp((scene.duration - frame) / 12)) * 1250;
	return (
		<AbsoluteFill>
			{scene.props.map((p, i) => {
				if (frame < p.at || (p.until !== undefined && frame >= p.until)) return null;
				const {x, y} = posAt(p.keys, frame);
				const s = spring({frame: frame - p.at, fps, config: {damping: 9, stiffness: 150}});
				const out = p.until === undefined ? 1 : clamp((p.until - frame) / 8);
				const bob = p.float ? Math.sin((frame + i * 19) / 13) * 10 : 0;
				const roll = p.hero.value === 'ball' ? (x - p.keys[0].x) * 0.8 : 0;
				return (
					<div key={`p${i}`} style={{position: 'absolute', inset: 0, transform: `scale(${s * out}) rotate(${roll}deg)`, transformOrigin: `${x}px ${y}px`}}>
						<HeroView hero={p.hero} x={x} y={y + bob} size={p.size} blink={blinkAt(frame, i + 9)} />
					</div>
				);
			})}
			{scene.actors.map((a, i) => {
				if (!visible(a)) return null;
				const pose = poses[i];
				const lift = clamp((pose.feetY - pose.y) / 200);
				return (
					<div key={`a${i}`}>
						{a.fly && pose.feetY < 880 ? null : (
							<div
								style={{
									position: 'absolute',
									left: pose.x - a.size * 0.24,
									top: pose.feetY - 16,
									width: a.size * 0.48,
									height: 30,
									borderRadius: '50%',
									background: 'rgba(0,0,0,0.14)',
									transform: `scale(${1 - lift * 0.5})`,
								}}
							/>
						)}
						{dustFrames(a).map((t) => (frame >= t && frame < t + 18 ? <Dust key={t} x={pose.x} y={pose.feetY} d={frame - t} /> : null))}
						<div
							style={{
								position: 'absolute',
								inset: 0,
								transform: `rotate(${pose.rot}deg) scale(${pose.sx}, ${pose.sy})`,
								transformOrigin: `${pose.x}px ${pose.y - (Math.abs(pose.rot) > 20 ? a.size / 2 : 0)}px`,
							}}
						>
							<Character
								hero={a.hero}
								x={pose.x}
								feetY={pose.y}
								height={a.size}
								pose={{blink: pose.sleeping ? 0.07 : blinkAt(frame, i + 5), talk: pose.talk, walk: pose.walk, arms: pose.arms, frame: frame + i * 7}}
							/>
						</div>
						{pose.sleeping ? <Zzz x={pose.x + a.size * 0.18} y={pose.y - a.size * 0.95} frame={frame} /> : null}
					</div>
				);
			})}
			{scene.bubbles.map((b, i) => {
				if (frame < b.at || frame >= b.until) return null;
				const a = scene.actors[b.actor];
				const pose = poses[b.actor];
				const s = spring({frame: frame - b.at, fps, config: {damping: 10, stiffness: 180}}) * clamp((b.until - frame) / 6);
				return <SpeechBubble key={`b${i}`} text={b.text} color={b.color} x={pose.x} y={pose.y - a.size + 20} scale={s} />;
			})}
			{scene.title && frame >= scene.title.at && frame < scene.title.until ? (
				<div style={{position: 'absolute', top: 60, width: '100%', opacity: clamp((scene.title.until - frame) / 10)}}>
					<PopWord text={scene.title.text} color={RAINBOW} size={130} startFrame={scene.title.at} />
				</div>
			) : null}
			{iris < 1250 ? <AbsoluteFill style={{background: `radial-gradient(circle at 50% 50%, transparent ${iris}px, #21173d ${iris + 1}px)`}} /> : null}
		</AbsoluteFill>
	);
};

export const Shards: React.FC<{x: number; y: number; at: number; color: string}> = ({x, y, at, color}) => {
	const frame = useCurrentFrame();
	const t = frame - at;
	if (t < 0 || t > 50) return null;
	return (
		<svg style={{position: 'absolute', inset: 0, overflow: 'visible'}} width={1920} height={1080}>
			{Array.from({length: 12}, (_, i) => {
				const a = -Math.PI * (0.1 + 0.8 * hash(i + 3));
				const v = 14 + hash(i + 9) * 12;
				const px = x + Math.cos(a) * v * t * (i % 2 ? 1 : -1);
				const py = y + Math.sin(a) * v * t + 0.6 * t * t;
				return (
					<path
						key={i}
						d={`M${px} ${py - 18} L${px + 16} ${py + 10} L${px - 14} ${py + 12} Z`}
						fill={color}
						stroke="#fff"
						strokeWidth={3}
						opacity={clamp((50 - t) / 15)}
						transform={`rotate(${t * 12 * (i % 2 ? 1 : -1)} ${px} ${py})`}
					/>
				);
			})}
		</svg>
	);
};

export const EggScene: React.FC<{scene: Extract<FunScene, {type: 'egg'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const drop = spring({frame, fps, config: {damping: 9, stiffness: 90}});
	let rot = 0;
	let cracked = 0;
	scene.ticks.forEach((t, i) => {
		if (frame >= t) {
			rot += Math.sin((frame - t) * 0.9) * 14 * Math.exp(-(frame - t) / 10);
			cracked = (i + clamp((frame - t) / 6)) / scene.ticks.length;
		}
	});
	const open = clamp((frame - scene.openAt) / 18);
	const rise = spring({frame: frame - scene.openAt, fps, config: {damping: 8, stiffness: 110}});
	const out = scene.duration - 14;
	const gone = clamp((frame - out) / 12);
	const eggY = interpolate(drop, [0, 1], [-500, 640]);
	const blink = blinkAt(frame, scene.from);
	return (
		<AbsoluteFill>
			{frame >= scene.openAt ? <Rays x={960} y={560} r={620} color="#fff6b0" opacity={rise * (1 - gone) * 0.8} frame={frame} /> : null}
			<div style={{position: 'absolute', top: 50, width: '100%', opacity: 1 - gone}}>
				{frame < scene.name.at ? (
					<PopWord text="What's inside?" color={RAINBOW} size={140} startFrame={6} />
				) : (
					<PopWord text={scene.name.text} color={scene.name.color} size={170} startFrame={scene.name.at} />
				)}
			</div>
			{open < 1 || frame < scene.openAt + 30 ? (
				<div style={{position: 'absolute', inset: 0, transform: `rotate(${rot}deg)`, transformOrigin: `960px ${eggY + 260}px`, opacity: 1 - gone}}>
					<div style={{position: 'absolute', left: 960 - 200, top: eggY - 260}}>
						<EggView value={scene.egg.value} color={scene.egg.color} size={520} crack={cracked} open={open} id={`e${scene.from}`} />
					</div>
				</div>
			) : null}
			<Shards x={960} y={600} at={scene.openAt} color={scene.egg.color} />
			{frame >= scene.openAt ? (
				<div style={{position: 'absolute', inset: 0, transform: `scale(${rise * (1 - gone)})`, transformOrigin: '960px 640px'}}>
					<HeroView hero={scene.hero} x={960} y={interpolate(rise, [0, 1], [700, 560])} size={430} blink={blink} />
				</div>
			) : null}
			<Confetti x={960} y={560} at={scene.openAt} count={44} />
			{scene.bubble && frame >= scene.bubble.at ? (
				<SpeechBubble
					text={scene.bubble.text}
					color={scene.bubble.color}
					x={1500}
					y={560}
					size={90}
					scale={spring({frame: frame - scene.bubble.at, fps, config: {damping: 10}}) * (1 - gone)}
				/>
			) : null}
		</AbsoluteFill>
	);
};

export const ShadowScene: React.FC<{scene: Extract<FunScene, {type: 'shadow'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const enter = spring({frame, fps, config: {damping: 10, stiffness: 120}});
	const light = clamp((frame - scene.revealAt) / 10);
	const bounce = frame >= scene.revealAt ? 1 + 0.22 * Math.exp(-(frame - scene.revealAt) / 8) : 1;
	const out = scene.duration - 14;
	const gone = clamp((frame - out) / 12);
	const bob = Math.sin(frame / 12) * 10;
	return (
		<AbsoluteFill>
			{light > 0 ? <Rays x={960} y={580} r={640} color="#fff6b0" opacity={light * (1 - gone) * 0.8} frame={frame} /> : null}
			<div style={{position: 'absolute', top: 50, width: '100%', opacity: 1 - gone}}>
				{frame < scene.name.at ? (
					<PopWord text="Who am I?" color={RAINBOW} size={150} startFrame={4} />
				) : (
					<PopWord text={scene.name.text} color={scene.name.color} size={170} startFrame={scene.name.at} />
				)}
			</div>
			<div
				style={{
					position: 'absolute',
					inset: 0,
					transform: `translateY(${bob}px) scale(${enter * bounce * (1 - gone)})`,
					transformOrigin: '960px 580px',
					filter: light < 1 ? `brightness(${light})` : undefined,
				}}
			>
				<HeroView hero={scene.hero} x={960} y={580} size={500} blink={light < 1 ? 1 : blinkAt(frame, scene.from)} />
			</div>
			{frame < scene.revealAt
				? [
						[560, 420],
						[1360, 380],
						[1420, 760],
					].map(([x, y], i) => (
						<div key={i} style={{position: 'absolute', left: x - 60, top: y - 90 + Math.sin((frame + i * 20) / 10) * 18, opacity: enter}}>
							<span style={textStyle(RAINBOW[(i * 2) % 7], 170)}>?</span>
						</div>
					))
				: null}
			{scene.counts.map((t, i) => {
				const d = frame - t;
				if (d < 0 || d > 26) return null;
				const s = spring({frame: d, fps, config: {damping: 8}});
				return (
					<div key={i} style={{position: 'absolute', left: 1500, top: 420, opacity: clamp((26 - d) / 8), transform: `scale(${s})`}}>
						<span style={textStyle(RAINBOW[i * 2], 260)}>{3 - i}</span>
					</div>
				);
			})}
			<Confetti x={960} y={560} at={scene.revealAt} count={40} />
			{scene.bubble && frame >= scene.bubble.at ? (
				<SpeechBubble
					text={scene.bubble.text}
					color={scene.bubble.color}
					x={1500}
					y={560}
					size={90}
					scale={spring({frame: frame - scene.bubble.at, fps, config: {damping: 10}}) * (1 - gone)}
				/>
			) : null}
		</AbsoluteFill>
	);
};

const move = (name: string, b: number, i: number) => {
	const p = ((b % 1) + 1) % 1;
	let x = 0;
	let y = 0;
	let rot = 0;
	let sx = 1;
	let sy = 1;
	switch (name) {
		case 'bounce':
			y = -Math.abs(Math.sin(Math.PI * b)) * 70;
			if (p < 0.14) {
				sx = 1.1;
				sy = 0.9;
			}
			break;
		case 'sway':
			x = Math.sin((Math.PI * b) / 2) * 60;
			rot = Math.sin((Math.PI * b) / 2) * 14;
			break;
		case 'spin': {
			const q = ((b % 4) + 4) % 4;
			rot = q > 3 ? 360 * (q - 3) : 0;
			y = -Math.abs(Math.sin(Math.PI * b)) * 30;
			break;
		}
		case 'jump': {
			const q = (((b + i * 0.5) % 2) + 2) % 2;
			y = -Math.sin((Math.PI * q) / 2) * 170;
			break;
		}
		case 'wiggle':
			rot = Math.sin(Math.PI * 2 * b) * 16;
			sx = 1 + Math.sin(Math.PI * 4 * b) * 0.05;
			break;
		case 'pop': {
			const k = 1 + 0.18 * Math.exp(-p * 6);
			sx = k;
			sy = k;
			break;
		}
	}
	return {x, y, rot, sx, sy};
};

export const DanceScene: React.FC<{scene: Extract<FunScene, {type: 'dance'}>}> = ({scene}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const freeze = scene.freezes.find((z) => frame >= z.at && frame < z.until);
	const f = freeze ? freeze.at : frame;
	const b = ((f - scene.beat0) * scene.bpm) / (60 * fps);
	const pulse = freeze ? 0.15 : Math.exp(-(((b % 1) + 1) % 1) * 5);
	const n = scene.crew.length;
	const enter = spring({frame, fps, config: {damping: 11, stiffness: 120}});
	const out = clamp((scene.duration - 10 - frame) / 10);

	// [x, feet y, height] of each dancer
	const place = (i: number): [number, number, number] => {
		switch (scene.formation) {
			case 'center':
				return i === 0 ? [960, 960, 600] : [960 + (i % 2 ? -1 : 1) * (460 + Math.floor((i - 1) / 2) * 290), 980, 400];
			case 'circle': {
				const a = (i / n) * Math.PI * 2 + f / 60;
				return [960 + Math.cos(a) * 600, 900 + Math.sin(a) * 90, 400 + Math.sin(a) * 90];
			}
			case 'conga': {
				const span = 2400;
				const x = ((f * 5 + i * 340) % span) - 240;
				return [x, 960, 440];
			}
			default: {
				const spacing = Math.min(440, 1760 / n);
				return [960 + (i - (n - 1) / 2) * spacing, 960, Math.min(540, spacing * 1.3)];
			}
		}
	};
	const armsFor = (k: number): Pose['arms'] => {
		const m = scene.moves[0];
		if (freeze) return 'up';
		if (m === 'pop') return 'clap';
		if (m === 'jump' || m === 'spin' || m === 'wiggle') return 'up';
		return Math.floor(b / 2 + k) % 2 ? 'up' : 'swing';
	};

	const order = scene.crew.map((_, i) => i).sort((a, c) => place(a)[2] - place(c)[2]);
	return (
		<AbsoluteFill>
			{RAINBOW.slice(0, 5).map((c, i) => {
				const a = Math.sin(f / 40 + i * 1.3) * 30 + (i - 2) * 22;
				return (
					<div
						key={c}
						style={{
							position: 'absolute',
							left: 960 - 160,
							top: -200,
							width: 320,
							height: 1500,
							background: `linear-gradient(${c}99, transparent 75%)`,
							transform: `rotate(${a}deg)`,
							transformOrigin: '50% 0%',
							opacity: 0.35 + pulse * 0.45,
						}}
					/>
				);
			})}
			{[0, 1, 2, 3, 4, 5].map((i) => (
				<div
					key={i}
					style={{
						position: 'absolute',
						left: hash(i + 3) * 1700,
						top: 80 + hash(i + 8) * 600,
						width: 160,
						height: 160,
						borderRadius: '50%',
						background: RAINBOW[i],
						opacity: 0.2 + pulse * 0.35,
						filter: 'blur(30px)',
						transform: `scale(${1 + pulse * 0.4})`,
					}}
				/>
			))}
			<svg style={{position: 'absolute', bottom: 0}} width={1920} height={260} viewBox="0 0 1920 260">
				{Array.from({length: 12}, (_, k) => (
					<rect
						key={k}
						x={k * 160}
						y={150}
						width={160}
						height={110}
						fill={RAINBOW[(k + Math.floor(b)) % 7]}
						opacity={0.45 + (k % 2 === Math.floor(b) % 2 ? pulse * 0.5 : 0.05)}
					/>
				))}
			</svg>
			{order.map((i) => {
				const [x, y, size] = place(i);
				const mv = scene.moves.reduce(
					(acc, name, k) => {
						const m = move(name, scene.formation === 'wave' ? b - i * 0.25 : b, i + k);
						return {x: acc.x + m.x, y: acc.y + m.y, rot: acc.rot + m.rot, sx: acc.sx * m.sx, sy: acc.sy * m.sy};
					},
					{x: 0, y: 0, rot: 0, sx: 1, sy: 1},
				);
				const s = enter * out;
				return (
					<div
						key={i}
						style={{
							position: 'absolute',
							inset: 0,
							transform: `translate(${mv.x}px, ${mv.y}px) rotate(${mv.rot}deg) scale(${s * mv.sx}, ${s * mv.sy})`,
							transformOrigin: `${x}px ${y - (scene.moves.includes('spin') ? size / 2 : 0)}px`,
						}}
					>
						<div
							style={{
								position: 'absolute',
								left: x - size * 0.22,
								top: y - 14,
								width: size * 0.44,
								height: 28,
								borderRadius: '50%',
								background: 'rgba(0,0,0,0.35)',
								transform: `translateY(${-mv.y}px) scale(${1 + mv.y / 400})`,
							}}
						/>
						{scene.crew[i].kind === 'balloon' ? (
							<HeroView hero={scene.crew[i]} x={x} y={y - size * 0.5} size={size * 0.9} blink={freeze ? 1 : blinkAt(frame, i + 2)} />
						) : (
							<Character
								hero={scene.crew[i]}
								x={x}
								feetY={y}
								height={size}
								pose={{blink: freeze ? 1 : blinkAt(frame, i + 2), walk: freeze ? 0 : b * Math.PI, arms: armsFor(i), frame: f + i * 5}}
							/>
						)}
					</div>
				);
			})}
			{scene.callouts.map((c, i) =>
				frame >= c.at && frame < c.at + 54 ? (
					<div key={i} style={{position: 'absolute', top: 60, width: '100%', opacity: clamp((c.at + 54 - frame) / 8)}}>
						<PopWord text={c.text} color={c.color} size={150} startFrame={c.at} />
					</div>
				) : null,
			)}
			{freeze ? <AbsoluteFill style={{background: 'rgba(120,200,255,0.18)'}} /> : null}
		</AbsoluteFill>
	);
};
