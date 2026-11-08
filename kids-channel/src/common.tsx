import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Fredoka';
import {Balloon, Face, mix} from './shapes';

export const {fontFamily} = loadFont('normal', {weights: ['600', '700'], subsets: ['latin']});

export const RAINBOW = ['#FF3B3B', '#FF8A1F', '#FFC92E', '#3CC75A', '#2F8CFF', '#9B5CFF', '#FF6FB5'];

/** Eyes close for 4 frames every ~3.5s; offset staggers characters. */
export const blinkAt = (frame: number, offset = 0) => {
	const p = (frame + offset * 37) % 105;
	return p < 4 ? Math.abs(p - 2) / 2 + 0.05 : 1;
};

export const textStyle = (color: string, size: number): React.CSSProperties => ({
	fontFamily,
	fontWeight: 700,
	fontSize: size,
	color,
	WebkitTextStroke: `${Math.round(size / 9)}px #fff`,
	paintOrder: 'stroke fill',
	filter: 'drop-shadow(0 8px 0 rgba(0,0,0,0.12))',
	lineHeight: 1,
	whiteSpace: 'nowrap',
});

/** Fluffy cloud with a soft blue underside. */
export const Cloud: React.FC<{x: number; y: number; s: number; color?: string; shade?: string}> = ({x, y, s, color = '#ffffff', shade = '#d6ecfa'}) => {
	const puffs = (
		<>
			<circle cx={70} cy={75} r={42} />
			<circle cx={125} cy={55} r={52} />
			<circle cx={185} cy={75} r={40} />
			<rect x={60} y={70} width={140} height={47} rx={23} />
		</>
	);
	return (
		<svg style={{position: 'absolute', left: x, top: y, overflow: 'visible'}} width={260 * s} height={130 * s} viewBox="0 0 260 130">
			<g fill={shade} transform="translate(0 8)">{puffs}</g>
			<g fill={color}>{puffs}</g>
		</svg>
	);
};

const Sun: React.FC<{x: number; y: number; frame: number}> = ({x, y, frame}) => (
	<svg style={{position: 'absolute', left: x - 170, top: y - 170, overflow: 'visible'}} width={340} height={340} viewBox="0 0 340 340">
		<defs>
			<radialGradient id="sun-glow">
				<stop offset="35%" stopColor="#fff3a8" stopOpacity={0.9} />
				<stop offset="100%" stopColor="#fff3a8" stopOpacity={0} />
			</radialGradient>
		</defs>
		<circle cx={170} cy={170} r={170} fill="url(#sun-glow)" />
		<g transform={`rotate(${frame * 0.5} 170 170)`}>
			{Array.from({length: 12}, (_, i) => (
				<path key={i} d="M164 52 L170 26 L176 52 Z" fill="#ffc21a" stroke="#ffc21a" strokeWidth={8} strokeLinejoin="round" transform={`rotate(${i * 30} 170 170)`} />
			))}
		</g>
		<circle cx={170} cy={170} r={86} fill="#ffd23f" />
		<circle cx={170} cy={170} r={86} fill="none" stroke="#ffb703" strokeWidth={6} opacity={0.5} />
		<ellipse cx={138} cy={136} rx={18} ry={26} fill="#fff" opacity={0.35} transform="rotate(-30 138 136)" />
		<Face x={170} y={176} scale={0.75} blink={blinkAt(frame, 7)} />
	</svg>
);

export type LandColors = {
	far: string;
	farTree: string;
	mid: [string, string];
	front: [string, string];
	tuft: string;
	flowers: boolean;
};

// ---------------------------------------------------------------- the look of a video: season and a seed
// Every video gets a season from its date and a seed, so skies, hills and trees are not the same picture every day.
export type Season = 'spring' | 'summer' | 'autumn' | 'winter';
export const Look = React.createContext<{season: Season; seed: number}>({season: 'spring', seed: 0});

/** Leaf colours for trees and bushes in each season. */
export const LEAVES: Record<Season, string[]> = {
	spring: ['#3fae4f', '#36a04a', '#5cc24b'],
	summer: ['#2f9e44', '#279038', '#3cb04a'],
	autumn: ['#e8963a', '#d9612f', '#e9b53a'],
	winter: ['#7fa58f', '#6d957f', '#8fb39c'],
};

const SKIES: Record<Season, string[]> = {
	spring: ['linear-gradient(#5cbdff 0%, #a6e0ff 55%, #e8f8ff 100%)', 'linear-gradient(#7aa8ff 0%, #ffc9d9 70%, #ffe9c9 100%)', 'linear-gradient(#4aa8f0 0%, #ffd9a0 80%, #fff0d0 100%)'],
	summer: ['linear-gradient(#3fb0ff 0%, #8fd8ff 60%, #e0f6ff 100%)', 'linear-gradient(#4aa8f0 0%, #ffd9a0 80%, #fff0d0 100%)'],
	autumn: ['linear-gradient(#6fb8f0 0%, #ffd8a8 70%, #fff0d8 100%)', 'linear-gradient(#89b9e0 0%, #f6d6b8 70%, #fdeede 100%)', 'linear-gradient(#5cbdff 0%, #ffe0b0 75%, #fff4e0 100%)'],
	winter: ['linear-gradient(#9fc9ee 0%, #dcecf8 60%, #f6fbff 100%)', 'linear-gradient(#b8c9e0 0%, #e8eef6 70%, #ffffff 100%)'],
};

export const DAY_LAND: LandColors = {
	far: '#b9e6c9',
	farTree: '#93d3a8',
	mid: ['#97e07a', '#74cc5a'],
	front: ['#62c74f', '#43a83a'],
	tuft: '#3f9e36',
	flowers: true,
};

const SEASON_LAND: Record<Season, LandColors> = {
	spring: DAY_LAND,
	summer: {far: '#a8e0a0', farTree: '#7cc98c', mid: ['#7fd35a', '#5cbf43'], front: ['#4cb83f', '#349a30'], tuft: '#2f8a2a', flowers: true},
	autumn: {far: '#ead2a2', farTree: '#d9a05b', mid: ['#e2b552', '#c99536'], front: ['#c9a440', '#a8812e'], tuft: '#8a6a2a', flowers: false},
	winter: {far: '#eef4fb', farTree: '#b9cbe0', mid: ['#ffffff', '#e8f0f8'], front: ['#fbfdff', '#e2ebf5'], tuft: '#b7c8da', flowers: false},
};

/** Leaves drifting down (autumn) or snow falling (winter) over the whole picture. */
export const Weather: React.FC<{season: Season; frame: number}> = ({season, frame}) => {
	if (season !== 'autumn' && season !== 'winter') return null;
	const n = season === 'winter' ? 70 : 16;
	return (
		<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
			{Array.from({length: n}, (_, i) => {
				const r = (k: number) => {
					const x = Math.sin((i + k * 31) * 127.1 + 311.7) * 43758.5453;
					return x - Math.floor(x);
				};
				const speed = season === 'winter' ? 1.2 + r(1) * 1.4 : 1.6 + r(1) * 1.2;
				const y = ((r(2) * 1200 + frame * speed) % 1200) - 80;
				const x = r(3) * 1920 + Math.sin(frame / (30 + r(4) * 30) + i) * 50;
				return season === 'winter' ? (
					<circle key={i} cx={x} cy={y} r={3 + r(5) * 5} fill="#ffffff" opacity={0.85} />
				) : (
					<path key={i} d="M0 0 Q12 -12 24 0 Q12 12 0 0Z" fill={LEAVES.autumn[i % 3]} transform={`translate(${x} ${y}) rotate(${frame * 3 + i * 40})`} />
				);
			})}
		</svg>
	);
};

const Tulip: React.FC<{x: number; y: number; c: string}> = ({x, y, c}) => (
	<g transform={`translate(${x} ${y})`}>
		<path d="M0 0 Q2 -18 0 -34" stroke="#3a9a34" strokeWidth={4} fill="none" />
		<path d="M0 -14 Q12 -20 14 -30 Q4 -26 0 -14" fill="#4cb944" />
		<path d="M-10 -46 L-10 -34 Q0 -26 10 -34 L10 -46 L5 -40 L0 -48 L-5 -40 Z" fill={c} />
	</g>
);

const Daisy: React.FC<{x: number; y: number; c: string}> = ({x, y, c}) => (
	<g transform={`translate(${x} ${y})`}>
		{Array.from({length: 6}, (_, k) => (
			<ellipse key={k} cx={0} cy={-8} rx={5} ry={9} fill={c} transform={`rotate(${k * 60})`} />
		))}
		<circle r={6} fill="#ffb703" />
	</g>
);

/** Rolling hills in three layers with little trees, grass tufts and flowers. */
export const Land: React.FC<{c: LandColors}> = ({c}) => (
	<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080} viewBox="0 0 1920 1080">
		<defs>
			<linearGradient id="land-mid" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stopColor={c.mid[0]} />
				<stop offset="100%" stopColor={c.mid[1]} />
			</linearGradient>
			<linearGradient id="land-front" x1="0" y1="0" x2="0" y2="1">
				<stop offset="0%" stopColor={c.front[0]} />
				<stop offset="100%" stopColor={c.front[1]} />
			</linearGradient>
		</defs>
		<path d="M0 770 Q 260 660 560 735 T 1160 725 T 1920 700 L1920 1080 L0 1080 Z" fill={c.far} />
		{[
			[110, 742],
			[190, 726],
			[1290, 712],
			[1420, 716],
			[1520, 706],
			[1760, 700],
		].map(([x, y], i) => (
			<g key={i}>
				<rect x={x - 4} y={y - 6} width={8} height={20} fill={c.farTree} />
				<circle cx={x} cy={y - 16} r={i % 2 ? 18 : 24} fill={c.farTree} />
			</g>
		))}
		<path d="M0 900 Q 380 780 820 890 T 1920 860 L1920 1080 L0 1080 Z" fill="url(#land-mid)" />
		<path d="M0 980 Q 520 870 1060 970 T 1920 950 L1920 1080 L0 1080 Z" fill="url(#land-front)" />
		<path d="M0 980 Q 520 870 1060 970 T 1920 950" fill="none" stroke="#fff" strokeWidth={4} opacity={0.18} />
		{[60, 250, 470, 690, 900, 1180, 1390, 1600, 1810].map((x, i) => {
			const y = 1010 + (i % 3) * 18;
			return <path key={x} d={`M${x} ${y} l-8 -20 M${x} ${y} l0 -26 M${x} ${y} l8 -20`} stroke={c.tuft} strokeWidth={5} strokeLinecap="round" />;
		})}
		{c.flowers ? (
			<>
				<Tulip x={150} y={1040} c="#ff6fb5" />
				<Daisy x={330} y={1026} c="#ffffff" />
				<Tulip x={560} y={1050} c="#ffc92e" />
				<Daisy x={800} y={1046} c="#ffd6ec" />
				<Tulip x={1260} y={1052} c="#9b5cff" />
				<Daisy x={1490} y={1030} c="#ffffff" />
				<Tulip x={1700} y={1046} c="#ff3b3b" />
				<Daisy x={1880} y={1040} c="#fff3a8" />
			</>
		) : null}
	</svg>
);

/** A few birds gliding across the sky. */
export const Birds: React.FC<{frame: number; color?: string}> = ({frame, color = '#3a4a6b'}) => (
	<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
		{[0, 1, 2].map((i) => {
			const x = ((frame * (1.4 + i * 0.3) + i * 700) % 2400) - 200;
			const y = 170 + i * 70 + Math.sin(frame / 30 + i) * 20;
			const f = Math.sin(frame * 0.35 + i * 2) * 12;
			return (
				<path key={i} d={`M${x - 20} ${y - f * 0.4} Q${x - 10} ${y - 10 - f} ${x} ${y} Q${x + 10} ${y - 10 - f} ${x + 20} ${y - f * 0.4}`} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round" />
			);
		})}
	</svg>
);

const Butterflies: React.FC<{frame: number}> = ({frame}) => (
	<svg style={{position: 'absolute', inset: 0}} width={1920} height={1080}>
		{[
			['#ff6fb5', 260, 0],
			['#ffc92e', 1640, 2],
		].map(([c, x0, off]) => {
			const t = frame / 40 + (off as number);
			const x = (x0 as number) + Math.sin(t) * 160;
			const y = 860 + Math.sin(t * 2.3) * 50;
			const w = 0.25 + Math.abs(Math.sin(frame * 0.5 + (off as number)));
			return (
				<g key={c as string} transform={`translate(${x} ${y}) rotate(${Math.cos(t) * 20})`}>
					<g transform={`scale(${w} 1)`}>
						<ellipse cx={-11} cy={-6} rx={12} ry={10} fill={c as string} />
						<ellipse cx={11} cy={-6} rx={12} ry={10} fill={c as string} />
						<ellipse cx={-8} cy={8} rx={8} ry={7} fill={c as string} opacity={0.85} />
						<ellipse cx={8} cy={8} rx={8} ry={7} fill={c as string} opacity={0.85} />
					</g>
					<rect x={-2} y={-12} width={4} height={24} rx={2} fill="#2b2b3a" />
				</g>
			);
		})}
	</svg>
);

export const Background: React.FC<{tint: string | null}> = ({tint}) => {
	const frame = useCurrentFrame();
	const {width} = useVideoConfig();
	const {season, seed} = React.useContext(Look);
	const skies = SKIES[season];
	const clouds = [
		{y: 60, s: 1.1, speed: 0.6, off: 100},
		{y: 200, s: 0.7, speed: 0.9, off: 900},
		{y: 110, s: 0.9, speed: 0.45, off: 1500},
		{y: 290, s: 0.6, speed: 0.75, off: 600},
	];
	return (
		<AbsoluteFill style={{background: skies[seed % skies.length]}}>
			<Sun x={[1730, 260, 1460][seed % 3]} y={150 + (seed % 2) * 40} frame={frame} />
			{clouds.map((c, i) => {
				const span = width + 400;
				const x = ((c.off + frame * c.speed) % span) - 300;
				return <Cloud key={i} x={x} y={c.y} s={c.s} />;
			})}
			<Birds frame={frame} />
			{tint ? (
				<AbsoluteFill
					style={{background: `radial-gradient(circle at 50% 55%, ${mix(tint, '#ffffff', 0.35)} 0%, transparent 55%)`, opacity: 0.55}}
				/>
			) : null}
			<Land c={SEASON_LAND[season]} />
			{season === 'spring' || season === 'summer' ? <Butterflies frame={frame} /> : <Weather season={season} frame={frame} />}
		</AbsoluteFill>
	);
};

/** Letters pop in one by one; `color` may be a list to colour each letter. */
export const PopWord: React.FC<{text: string; color: string | string[]; size: number; startFrame: number}> = ({text, color, size, startFrame}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	let k = 0;
	return (
		<div style={{display: 'flex', justifyContent: 'center'}}>
			{text.split('').map((ch, i) => {
				const s = spring({frame: frame - startFrame - i * 3, fps, config: {damping: 9, stiffness: 160}});
				const wobble = Math.sin((frame + i * 8) / 9) * 6;
				const c = Array.isArray(color) ? color[(ch === ' ' ? k : k++) % color.length] : color;
				return (
					<span key={i} style={{...textStyle(c, size), display: 'inline-block', transform: `translateY(${wobble}px) scale(${s})`}}>
						{ch === ' ' ? ' ' : ch}
					</span>
				);
			})}
		</div>
	);
};

export const FloatingBalloon: React.FC<{color: string; x: number; y: number; width: number; enterAt?: number; seed?: number; exitAt?: number}> = ({
	color,
	x,
	y,
	width,
	enterAt = 0,
	seed = 0,
	exitAt,
}) => {
	const frame = useCurrentFrame();
	const {fps, height} = useVideoConfig();
	const enter = spring({frame: frame - enterAt, fps, config: {damping: 12, stiffness: 70}});
	const exit = exitAt === undefined ? 0 : interpolate(frame - exitAt, [0, 25], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
	const bob = Math.sin((frame + seed * 20) / 18) * 14;
	const rot = Math.sin((frame + seed * 13) / 24) * 5;
	const sway = Math.sin((frame + seed * 10) / 15) * 10;
	const ty = interpolate(enter, [0, 1], [height + 200, 0]) - exit * (height + 400) + bob;
	return (
		<div style={{position: 'absolute', left: x - width / 2, top: y, transform: `translateY(${ty}px) rotate(${rot}deg)`, transformOrigin: '50% 100%'}}>
			<Balloon color={color} width={width} blink={blinkAt(frame, seed)} sway={sway} />
		</div>
	);
};
