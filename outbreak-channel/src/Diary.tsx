import React from 'react';
import {AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont as loadAnton} from '@remotion/google-fonts/Anton';
import {loadFont as loadElite} from '@remotion/google-fonts/SpecialElite';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {C, Defs, H, W, clamp, hash} from './art';
import {FOCUS, Params, SCENES} from './scenes';

const anton = loadAnton('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const elite = loadElite('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
loadInter('normal', {weights: ['400', '800'], subsets: ['latin']});

// ---------------------------------------------------------------- props (written by scripts/diary.py)
type Chunk = {words: string[]; hl: boolean[]; at: number; until: number; talk?: boolean};
export type Beat = {
	from: number;
	duration: number;
	scene: string;
	p: Params;
	cam: 'push' | 'pull' | 'left' | 'right' | 'still';
	tone: 'night' | 'dawn' | 'dusk';
	rain: boolean;
	fog: boolean;
	flashlight: boolean;
	alarm: boolean;
	cutIn: boolean;
	cutOut: boolean;
	hits: number[];
};
export type DiaryProps = {
	durationInFrames: number;
	audio: string;
	day: number;
	series: string;
	title: string;
	beats: Beat[];
	chunks: Chunk[];
	endAt: number;
};

// ---------------------------------------------------------------- overlays
const Rain: React.FC<{f: number}> = ({f}) => (
	<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
		{Array.from({length: 90}, (_, i) => {
			const x = (hash(i) * 1300 + f * 6) % 1300 - 110;
			const y = (hash(i + 50) * 2100 + f * (38 + hash(i) * 20)) % 2100 - 100;
			return <line key={i} x1={x} y1={y} x2={x - 10} y2={y + 60} stroke="#b9c9e8" strokeWidth={2.5} opacity={0.22} />;
		})}
	</svg>
);

const Fog: React.FC<{f: number}> = ({f}) => (
	<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
		<defs>
			<filter id="fogblur" x="-50%" y="-50%" width="200%" height="200%">
				<feGaussianBlur stdDeviation="60" />
			</filter>
		</defs>
		<g filter="url(#fogblur)">
			{Array.from({length: 6}, (_, i) => (
				<ellipse key={i} cx={((hash(i) * 1600 + f * (0.8 + hash(i + 3))) % 1600) - 260} cy={1250 + hash(i + 9) * 600} rx={420} ry={140} fill="#7f8aa6" opacity={0.18} />
			))}
		</g>
	</svg>
);

const Grain: React.FC<{f: number}> = ({f}) => (
	<svg width={W} height={H} style={{position: 'absolute', inset: 0, mixBlendMode: 'overlay', opacity: 0.16}}>
		<filter id="grain">
			<feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 12} />
		</filter>
		<rect width={W} height={H} filter="url(#grain)" />
	</svg>
);

const Vignette: React.FC = () => <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.75) 100%)'}} />;

const TONES: Record<string, React.CSSProperties | null> = {
	night: null,
	dawn: {background: 'linear-gradient(#9fb2cf, #6d7f9c)', mixBlendMode: 'screen', opacity: 0.22},
	dusk: {background: 'linear-gradient(#ff8a4c, #8a2a4a)', mixBlendMode: 'overlay', opacity: 0.35},
};

// ---------------------------------------------------------------- one beat: a scene, a camera move and its overlays
const BeatView: React.FC<{b: Beat}> = ({b}) => {
	const f = useCurrentFrame();
	const t = f / Math.max(1, b.duration);
	const Scene = SCENES[b.scene];
	let s = 1.03;
	let tx = 0;
	if (b.cam === 'push') s = 1 + 0.09 * t;
	if (b.cam === 'pull') s = 1.09 - 0.09 * t;
	if (b.cam === 'left' || b.cam === 'right') {
		s = 1.08;
		tx = (b.cam === 'left' ? 1 : -1) * (50 - 100 * t);
	}
	let sx = 0;
	let sy = 0;
	for (const h of b.hits) {
		const d = f - h;
		if (d >= 0 && d < 16) {
			const k = Math.exp(-d / 5) * 18;
			sx += Math.sin(d * 2.1) * k;
			sy += Math.cos(d * 2.7) * k;
		}
	}
	const [ox, oy] = FOCUS[b.scene] ?? [540, 960];
	const fade = Math.max(b.cutIn ? 1 - clamp(f / 7) : 0, b.cutOut ? clamp((f - (b.duration - 5)) / 5) : 0);
	const lx = 540 + Math.sin(f / 23) * 260 + Math.sin(f / 9) * 30;
	const ly = 980 + Math.cos(f / 31) * 380;
	const tone = TONES[b.tone];
	return (
		<AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
			<AbsoluteFill style={{transform: `translate(${tx + sx}px, ${sy}px) scale(${s})`, transformOrigin: `${ox}px ${oy}px`}}>
				<svg width={0} height={0} style={{position: 'absolute'}}>
					<Defs />
				</svg>
				{Scene ? <Scene p={b.p} f={f} /> : null}
				{b.fog ? <Fog f={f} /> : null}
				{b.rain ? <Rain f={f} /> : null}
			</AbsoluteFill>
			{tone ? <AbsoluteFill style={tone} /> : null}
			{b.flashlight ? (
				<>
					<AbsoluteFill style={{background: `radial-gradient(circle at ${lx}px ${ly}px, rgba(255,240,205,0.5) 0px, rgba(255,240,205,0.12) 220px, rgba(255,240,205,0) 330px)`, mixBlendMode: 'screen'}} />
					<AbsoluteFill style={{background: `radial-gradient(circle at ${lx}px ${ly}px, rgba(0,0,0,0) 0px, rgba(0,0,0,0.15) 200px, rgba(0,0,0,0.93) 430px)`}} />
				</>
			) : null}
			{b.alarm ? <AbsoluteFill style={{background: C.red, mixBlendMode: 'multiply', opacity: 0.25 + 0.2 * Math.sin(f / 4)}} /> : null}
			{fade > 0 ? <AbsoluteFill style={{background: '#000', opacity: fade}} /> : null}
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- text
const Captions: React.FC<{chunks: Chunk[]}> = ({chunks}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const c = chunks.find((k) => f >= k.at && f < k.until);
	if (!c) return null;
	const pop = spring({frame: f - c.at, fps, config: {damping: 14, stiffness: 260}});
	return (
		<div style={{position: 'absolute', left: 70, right: 70, top: 1170, display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '0 26px', transform: `scale(${0.86 + 0.14 * pop})`}}>
			{c.words.map((w, i) => (
				<span
					key={i}
					style={{
						fontFamily: anton,
						fontSize: 112,
						lineHeight: 1.12,
						textTransform: 'uppercase',
						color: c.hl[i] ? C.red : c.talk ? '#ffe39a' : '#ffffff',
						WebkitTextStroke: '14px #000',
						paintOrder: 'stroke fill',
						textShadow: '0 10px 24px rgba(0,0,0,0.8)',
					}}
				>
					{w}
				</span>
			))}
		</div>
	);
};

const Intro: React.FC<{day: number; series: string; title: string}> = ({day, series, title}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const slam = spring({frame: f, fps, config: {damping: 12, stiffness: 220}});
	const out = clamp((f - 54) / 10);
	return (
		<div style={{position: 'absolute', top: 200, width: '100%', textAlign: 'center', opacity: 1 - out}}>
			<div style={{fontFamily: elite, fontSize: 40, letterSpacing: 8, color: '#d9d2c0'}}>OUTBREAK DIARY · {series.toUpperCase()}</div>
			<div style={{fontFamily: anton, fontSize: 230, color: '#fff', lineHeight: 1.05, transform: `scale(${2 - slam})`, textShadow: '0 12px 30px rgba(0,0,0,0.9)'}}>DAY {day}</div>
			<div style={{width: 300 * slam, height: 12, background: C.red, margin: '0 auto'}} />
			<div style={{fontFamily: elite, fontSize: 60, color: '#efe6d2', marginTop: 28, textShadow: '0 6px 20px rgba(0,0,0,0.9)'}}>{title}</div>
		</div>
	);
};

const TopLabel: React.FC<{day: number; series: string}> = ({day, series}) => {
	const f = useCurrentFrame();
	return (
		<div style={{position: 'absolute', top: 118, width: '100%', textAlign: 'center', fontFamily: elite, fontSize: 36, letterSpacing: 4, color: '#e6dccb', opacity: 0.75 * clamp((f - 64) / 12)}}>
			{series.toUpperCase()} · DAY {day}
		</div>
	);
};

const EndCard: React.FC<{day: number; endAt: number}> = ({day, endAt}) => {
	const f = useCurrentFrame() - endAt;
	if (f < 0) return null;
	const text = 'TO BE CONTINUED...';
	const shown = Math.floor(clamp(f / 30) * text.length);
	return (
		<AbsoluteFill style={{background: `rgba(0,0,0,${0.75 * clamp(f / 12)})`}}>
			<div style={{position: 'absolute', top: 760, width: '100%', textAlign: 'center', fontFamily: elite, fontSize: 76, color: '#efe6d2'}}>{text.slice(0, shown)}</div>
			<div style={{position: 'absolute', top: 900, width: '100%', textAlign: 'center', fontFamily: anton, fontSize: 84, color: C.red, opacity: clamp((f - 34) / 8)}}>
				FOLLOW FOR DAY {day + 1}
			</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- composition
export const Diary: React.FC<DiaryProps> = ({beats, chunks, audio, day, series, title, endAt}) => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: '#000'}}>
			{beats.map((b, i) => (
				<Sequence key={i} from={b.from} durationInFrames={b.duration}>
					<BeatView b={b} />
				</Sequence>
			))}
			<Vignette />
			<Grain f={f} />
			{f < 70 ? <Intro day={day} series={series} title={title} /> : <TopLabel day={day} series={series} />}
			<Captions chunks={chunks} />
			<EndCard day={day} endAt={endAt} />
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
	);
};
