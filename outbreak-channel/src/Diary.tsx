import React from 'react';
import {AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont as loadAnton} from '@remotion/google-fonts/Anton';
import {loadFont as loadElite} from '@remotion/google-fonts/SpecialElite';
import {loadFont as loadInter} from '@remotion/google-fonts/Inter';
import {loadFont as loadBebas} from '@remotion/google-fonts/BebasNeue';
import {loadFont as loadVT} from '@remotion/google-fonts/VT323';
import {loadFont as loadMarker} from '@remotion/google-fonts/PermanentMarker';
import {loadFont as loadRockSalt} from '@remotion/google-fonts/RockSalt';
import {loadFont as loadArchivo} from '@remotion/google-fonts/ArchivoBlack';
import {C, Defs, H, W, clamp, hash} from './art';
import {Params, SCENES, SHOTS} from './scenes';

const anton = loadAnton('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const elite = loadElite('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
loadInter('normal', {weights: ['400', '800'], subsets: ['latin']});
const latin = {weights: ['400'], subsets: ['latin']};
const bebas = loadBebas('normal', latin).fontFamily;
const vt = loadVT('normal', latin).fontFamily;
const marker = loadMarker('normal', latin).fontFamily;
const rocksalt = loadRockSalt('normal', latin).fontFamily;
const archivo = loadArchivo('normal', latin).fontFamily;

// Each story has its own look ("frame", story/series.json; a special takes the look of its kind):
//   diary      the survivor's diary: typewriter titles, big white captions
//   camcorder  a phone recording: REC light, timecode, viewfinder corners
//   journal    a handwritten journal: paper edges, tape, handwriting
//   broadcast  an emergency broadcast: LIVE banner, news ticker, a narrow radio voice
export type Frame = 'diary' | 'camcorder' | 'journal' | 'broadcast';
type FrameStyle = {caption: string; size: number; title: string; titleSize: number; label: string; paper: string; capTop: number};
const FRAMES: Record<Frame, FrameStyle> = {
	diary: {caption: anton, size: 112, title: elite, titleSize: 60, label: elite, paper: '#efe6d2', capTop: 1170},
	camcorder: {caption: bebas, size: 128, title: vt, titleSize: 76, label: vt, paper: '#e8f4e8', capTop: 1170},
	journal: {caption: marker, size: 100, title: rocksalt, titleSize: 52, label: marker, paper: '#f1e4c4', capTop: 1150},
	broadcast: {caption: archivo, size: 92, title: archivo, titleSize: 56, label: archivo, paper: '#ffffff', capTop: 1080},
};

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
	seed?: number; // changes crowds and details from part to part
	place?: number; // the same in every part of a story: its doors, lift, radio...
	shot?: number; // which of the scene's SHOTS the camera frames: 0 is wide
	flip?: boolean; // mirror the scene
};
export type DiaryProps = {
	durationInFrames: number;
	audio: string;
	day: number;
	series: string;
	label?: string | null; // a one-part special shows this instead of "DAY N"
	grade?: string | null; // the story's colour, laid softly over every scene
	title: string;
	frame?: Frame;
	tagline?: string | null; // one line for viewers who land in the middle of a story
	finale?: boolean; // the story's last day
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
	let move = 1.03;
	let pan = 0;
	if (b.cam === 'push') move = 1 + 0.09 * t;
	if (b.cam === 'pull') move = 1.09 - 0.09 * t;
	if (b.cam === 'left' || b.cam === 'right') {
		move = 1.08;
		pan = (b.cam === 'left' ? 1 : -1) * (50 - 100 * t);
	}
	// the shot: wide, or a close-up centred on one of the scene's points of interest
	const points = SHOTS[b.scene] ?? [[540, 960]];
	const shot = (b.shot ?? 0) % points.length;
	const [px0, py] = points[shot];
	const px = b.flip ? W - px0 : px0;
	const zoom = shot === 0 ? 1 : (b.shot ?? 0) % 2 ? 1.32 : 1.55;
	const s = zoom * move;
	// move the point towards the centre, but never so far that the edge of the picture shows
	const keep = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
	const tx = keep((shot === 0 ? 0 : 540 - px) + pan, W - px - (W - px) * s, px * s - px);
	const ty = keep(shot === 0 ? 0 : 960 - py, H - py - (H - py) * s, py * s - py);
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
	const fade = Math.max(b.cutIn ? 1 - clamp(f / 7) : 0, b.cutOut ? clamp((f - (b.duration - 5)) / 5) : 0);
	const lx = 540 + Math.sin(f / 23) * 260 + Math.sin(f / 9) * 30;
	const ly = 980 + Math.cos(f / 31) * 380;
	const tone = TONES[b.tone];
	return (
		<AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
			<AbsoluteFill style={{transform: `translate(${tx + sx}px, ${ty + sy}px) scale(${s})`, transformOrigin: `${px}px ${py}px`}}>
				<svg width={0} height={0} style={{position: 'absolute'}}>
					<Defs />
				</svg>
				<AbsoluteFill style={{transform: b.flip ? 'scaleX(-1)' : undefined}}>{Scene ? <Scene p={b.p} f={f} s={b.seed ?? 0} place={b.place ?? 0} /> : null}</AbsoluteFill>
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
const Captions: React.FC<{chunks: Chunk[]; frame: Frame}> = ({chunks, frame}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const st = FRAMES[frame];
	const c = chunks.find((k) => f >= k.at && f < k.until);
	if (!c) return null;
	const pop = spring({frame: f - c.at, fps, config: {damping: 14, stiffness: 260}});
	return (
		<div style={{position: 'absolute', left: 70, right: 70, top: st.capTop, display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: '0 26px', transform: `scale(${0.86 + 0.14 * pop}) rotate(${frame === 'journal' ? -2 : 0}deg)`, ...(frame === 'broadcast' ? {background: 'rgba(8,10,16,0.82)', padding: '18px 26px', borderLeft: `14px solid ${C.red}`} : {})}}>
			{c.words.map((w, i) => (
				<span
					key={i}
					style={{
						fontFamily: st.caption,
						fontSize: st.size,
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

// No title card: the first second decides whether a viewer stays, so the scene and the first line start at once and
// the story's name, the day and a one-line premise sit small at the top.
const Header: React.FC<{day: number; series: string; label?: string | null; tagline?: string | null; frame: Frame}> = ({day, series, label, tagline, frame}) => {
	const f = useCurrentFrame();
	const st = FRAMES[frame];
	const own = frame === 'camcorder' || frame === 'broadcast'; // their overlays already show the day or LIVE
	const tag = tagline ? clamp(1 - (f - 120) / 14) : 0;
	return (
		<div style={{position: 'absolute', top: own ? 270 : 150, width: '100%', textAlign: 'center', fontFamily: st.label, color: '#efe6d2', textShadow: '0 3px 12px rgba(0,0,0,0.95)'}}>
			{own ? null : (
				<div style={{fontSize: 42, letterSpacing: 4, opacity: 0.85}}>{label ? series.toUpperCase() : `${series.toUpperCase()} · DAY ${day}`}</div>
			)}
			{tag > 0 ? (
				<div style={{fontSize: frame === 'camcorder' ? 50 : 36, letterSpacing: 2, marginTop: 10, opacity: 0.8 * tag, padding: '0 90px'}}>{tagline!.toUpperCase()}</div>
			) : null}
		</div>
	);
};

const EndCard: React.FC<{day: number; endAt: number; label?: string | null; frame: Frame; finale?: boolean}> = ({day, endAt, label, frame, finale}) => {
	const f = useCurrentFrame() - endAt;
	if (f < 0) return null;
	const text = finale ? 'THE END' : frame === 'broadcast' ? 'END OF TRANSMISSION' : frame === 'camcorder' ? 'RECORDING STOPPED' : label ? 'THE END...?' : 'TO BE CONTINUED...';
	const shown = Math.floor(clamp(f / 30) * text.length);
	return (
		<AbsoluteFill style={{background: `rgba(0,0,0,${0.75 * clamp(f / 12)})`}}>
			<div style={{position: 'absolute', top: 760, width: '100%', textAlign: 'center', fontFamily: FRAMES[frame].title, fontSize: 76, color: FRAMES[frame].paper}}>{text.slice(0, shown)}</div>
			<div style={{position: 'absolute', top: 900, width: '100%', textAlign: 'center', fontFamily: anton, fontSize: 84, color: C.red, opacity: clamp((f - 34) / 8)}}>
				{label || finale ? 'FOLLOW FOR THE NEXT STORY' : `FOLLOW FOR DAY ${day + 1}`}
			</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- the frame overlays
const pad = (n: number) => String(Math.floor(n)).padStart(2, '0');

const Camcorder: React.FC<{day: number; label?: string | null}> = ({day, label}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const secs = 2 * 3600 + 14 * 60 + day * 97 + f / fps;
	const corner = (x: number, y: number, rx: number, ry: number) => (
		<path d={`M ${x} ${y + 90 * ry} L ${x} ${y} L ${x + 90 * rx} ${y}`} stroke="#fff" strokeWidth={8} fill="none" opacity={0.85} />
	);
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(0deg, rgba(255,255,255,0.035) 0 2px, transparent 2px 5px)'}} />
			<svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
				{corner(60, 150, 1, 1)}
				{corner(W - 60, 150, -1, 1)}
				{corner(60, H - 150, 1, -1)}
				{corner(W - 60, H - 150, -1, -1)}
				<rect x={W - 210} y={190} width={110} height={52} rx={8} stroke="#fff" strokeWidth={5} fill="none" />
				<rect x={W - 100} y={204} width={10} height={24} fill="#fff" />
				<rect x={W - 200} y={200} width={day % 3 === 0 ? 30 : 60} height={32} fill={day % 3 === 0 ? C.red : '#fff'} />
			</svg>
			<div style={{position: 'absolute', left: 100, top: 180, display: 'flex', alignItems: 'center', gap: 16, fontFamily: vt, fontSize: 64, color: '#fff'}}>
				<div style={{width: 34, height: 34, borderRadius: 17, background: C.red, opacity: f % 30 < 18 ? 1 : 0.15}} />
				REC
			</div>
			<div style={{position: 'absolute', left: 100, bottom: 190, fontFamily: vt, fontSize: 58, color: '#fff', letterSpacing: 2}}>
				{label ? 'FOUND FOOTAGE' : `DAY ${pad(day)}`}  {pad(secs / 3600)}:{pad((secs / 60) % 60)}:{pad(secs % 60)}
			</div>
		</AbsoluteFill>
	);
};

const Journal: React.FC = () => (
	<AbsoluteFill>
		<AbsoluteFill style={{background: '#b89b6a', mixBlendMode: 'multiply', opacity: 0.32}} />
		<AbsoluteFill style={{boxShadow: 'inset 0 0 0 30px #e9dcbc, inset 0 0 0 36px #c9b48a, inset 0 0 120px 60px rgba(60,40,10,0.55)'}} />
		{[
			[110, 120, -18],
			[W - 250, 130, 14],
			[120, H - 190, 10],
			[W - 260, H - 200, -12],
		].map(([x, y, r], i) => (
			<div key={i} style={{position: 'absolute', left: x, top: y, width: 150, height: 54, background: 'rgba(235,225,190,0.75)', transform: `rotate(${r}deg)`, boxShadow: '0 2px 6px rgba(0,0,0,0.3)'}} />
		))}
	</AbsoluteFill>
);

const TICKER = 'STAY INDOORS  ·  LOCK ALL DOORS  ·  DO NOT APPROACH THE INFECTED  ·  KEEP NOISE TO A MINIMUM  ·  LISTEN FOR FURTHER INSTRUCTIONS  ·  ';

const Broadcast: React.FC<{title: string}> = ({title}) => {
	const f = useCurrentFrame();
	const text = (title.toUpperCase() + '  ·  ' + TICKER).repeat(3);
	return (
		<AbsoluteFill>
			<AbsoluteFill style={{backgroundImage: 'repeating-linear-gradient(0deg, rgba(0,0,0,0.12) 0 2px, transparent 2px 4px)'}} />
			<div style={{position: 'absolute', top: 120, left: 0, right: 0, display: 'flex', justifyContent: 'center', gap: 18, alignItems: 'center'}}>
				<div style={{fontFamily: archivo, fontSize: 44, color: '#fff', background: C.red, padding: '6px 20px', opacity: f % 40 < 28 ? 1 : 0.55}}>LIVE</div>
				<div style={{fontFamily: archivo, fontSize: 44, color: '#111', background: '#ffd23f', padding: '6px 22px'}}>EMERGENCY BROADCAST</div>
			</div>
			<div style={{position: 'absolute', left: 0, right: 0, bottom: 150, height: 86, background: 'rgba(10,10,14,0.92)', borderTop: `6px solid ${C.red}`, overflow: 'hidden'}}>
				<div style={{position: 'absolute', top: 14, left: 1080 - ((f * 7) % 3400), whiteSpace: 'nowrap', fontFamily: archivo, fontSize: 46, color: '#fff'}}>{text}</div>
			</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- composition
export const Diary: React.FC<DiaryProps> = ({beats, chunks, audio, day, series, label, grade, title, endAt, frame = 'diary', tagline, finale}) => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: '#000'}}>
			{beats.map((b, i) => (
				<Sequence key={i} from={b.from} durationInFrames={b.duration}>
					<BeatView b={b} />
				</Sequence>
			))}
			{grade ? <AbsoluteFill style={{background: grade, mixBlendMode: 'soft-light', opacity: 0.5}} /> : null}
			<Vignette />
			<Grain f={f} />
			{frame === 'camcorder' ? <Camcorder day={day} label={label} /> : frame === 'journal' ? <Journal /> : frame === 'broadcast' ? <Broadcast title={title} /> : null}
			<Header day={day} series={series} label={label} tagline={tagline} frame={frame} />
			<Captions chunks={chunks} frame={frame} />
			<EndCard day={day} endAt={endAt} label={label} frame={frame} finale={finale} />
			{audio ? <Audio src={staticFile(audio)} /> : null}
		</AbsoluteFill>
	);
};
