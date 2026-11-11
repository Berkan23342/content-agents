import React from 'react';
import {AbsoluteFill, Audio, Freeze, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {loadFont as loadAnton} from '@remotion/google-fonts/Anton';
import {loadFont as loadElite} from '@remotion/google-fonts/SpecialElite';
import {C, clamp} from './art';
import {BeatView, Diary, DiaryProps} from './Diary';

// The full-story video of a finished story (scripts/film.py): 16:9, the vertical part in the middle, the day on the
// left, the season's days on the right; a narrated opening and an ending that points to the next story.

const anton = loadAnton('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;
const elite = loadElite('normal', {weights: ['400'], subsets: ['latin']}).fontFamily;

type FilmPart = {from: number; gap: number; duration: number; day: number; title: string; props: DiaryProps};
export type FilmProps = {
	durationInFrames: number;
	audio: string;
	series: string;
	title: string;
	tagline?: string | null;
	grade?: string | null;
	days: number;
	intro: {duration: number};
	parts: FilmPart[];
	outro: {from: number; duration: number; next?: {name: string; tagline?: string | null} | null};
};

const FW = 1920;
const FH = 1080;
const S = FH / 1920; // the vertical part, scaled to the film's height
const BOX = 1080 * S;
const BOX_X = (FW - BOX) / 2;
const PAPER = '#efe6d2';

const Backdrop: React.FC<{grade?: string | null}> = ({grade}) => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: `radial-gradient(ellipse at 50% 45%, ${grade ?? '#3b6fb6'}38 0%, #0a0b12 55%, #050509 100%)`}}>
			<svg width={FW} height={FH} style={{position: 'absolute', inset: 0, mixBlendMode: 'overlay', opacity: 0.14}}>
				<filter id="filmgrain">
					<feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves={2} seed={f % 12} />
				</filter>
				<rect width={FW} height={FH} filter="url(#filmgrain)" />
			</svg>
		</AbsoluteFill>
	);
};

const typed = (text: string, f: number, speed = 1.4) => text.slice(0, Math.floor(Math.max(0, f) * speed));

// A still of the story's first place, in a vertical box (the opening and the thumbnail).
const Poster: React.FC<{p: FilmProps; height: number; right: number}> = ({p, height, right}) => {
	const first = p.parts[0]?.props;
	const beat = first?.beats.find((b) => b.scene !== 'phone' && b.scene !== 'supplies') ?? first?.beats[0];
	if (!beat) return null;
	const s = height / 1920;
	return (
		<div style={{position: 'absolute', right, top: 0, width: 1080 * s, height, overflow: 'hidden', boxShadow: '0 0 80px rgba(0,0,0,0.9)'}}>
			<div style={{position: 'absolute', width: 1080, height: 1920, transform: `scale(${s})`, transformOrigin: '0 0'}}>
				<Freeze frame={40}>
					<BeatView b={{...beat, cutIn: false, cutOut: false, hits: [], shot: 0}} />
				</Freeze>
				{p.grade ? <AbsoluteFill style={{background: p.grade, mixBlendMode: 'soft-light', opacity: 0.5}} /> : null}
				<AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 45%, rgba(0,0,0,0.7) 100%)'}} />
			</div>
		</div>
	);
};

const Intro: React.FC<{p: FilmProps}> = ({p}) => {
	const f = useCurrentFrame();
	const show = (at: number) => clamp((f - at) / 12);
	return (
		<AbsoluteFill>
			<div style={{opacity: show(0)}}>
				<Poster p={p} height={FH} right={150} />
			</div>
			<div style={{position: 'absolute', left: 150, top: 250, width: 980}}>
				<div style={{fontFamily: anton, fontSize: 46, letterSpacing: 8, color: C.red, opacity: show(4)}}>THE FULL STORY</div>
				<div style={{fontFamily: elite, fontSize: 52, color: PAPER, marginTop: 18, opacity: 0.85 * show(10)}}>{p.series.toUpperCase()}</div>
				<div style={{fontFamily: anton, fontSize: p.title.length > 30 ? 104 : 124, lineHeight: 1.04, color: '#fff', marginTop: 26, textTransform: 'uppercase', opacity: show(18), transform: `translateY(${(1 - show(18)) * 30}px)`}}>
					{p.title}
				</div>
				<div style={{fontFamily: elite, fontSize: 46, color: PAPER, marginTop: 34, opacity: 0.9 * show(40)}}>{`ALL ${p.days} DAYS · ONE VIDEO`}</div>
			</div>
		</AbsoluteFill>
	);
};

const DayCard: React.FC<{day: number; title: string}> = ({day, title}) => {
	const f = useCurrentFrame();
	return (
		<AbsoluteFill style={{background: '#000', justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
			<div style={{fontFamily: elite, fontSize: 150, color: PAPER}}>{typed(`DAY ${day}`, f, 0.6)}</div>
			<div style={{fontFamily: elite, fontSize: 70, color: PAPER, opacity: 0.75 * clamp((f - 14) / 10), marginTop: 30, padding: '0 80px'}}>{title.toUpperCase()}</div>
		</AbsoluteFill>
	);
};

const Part: React.FC<{p: FilmProps; part: FilmPart}> = ({p, part}) => {
	const f = useCurrentFrame();
	const rowH = Math.min(52, 880 / p.days);
	return (
		<AbsoluteFill>
			{/* left: where we are */}
			<div style={{position: 'absolute', left: 60, width: BOX_X - 130, top: 250, textAlign: 'right', color: PAPER}}>
				<div style={{fontFamily: elite, fontSize: 38, letterSpacing: 4, opacity: 0.75}}>{p.series.toUpperCase()}</div>
				<div style={{fontFamily: anton, fontSize: 64, letterSpacing: 6, color: C.red, marginTop: 40}}>DAY</div>
				<div style={{fontFamily: anton, fontSize: 260, lineHeight: 0.95, color: '#fff'}}>{part.day}</div>
				<div style={{fontFamily: elite, fontSize: 40, marginTop: 24, lineHeight: 1.25}}>{part.title.toUpperCase()}</div>
				<div style={{fontFamily: elite, fontSize: 30, marginTop: 18, opacity: 0.6}}>{`OF ${p.days}`}</div>
			</div>
			{/* the part itself */}
			<div style={{position: 'absolute', left: BOX_X, top: 0, width: BOX, height: FH, overflow: 'hidden', boxShadow: '0 0 80px rgba(0,0,0,0.9)'}}>
				<div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: 1920, transform: `scale(${S})`, transformOrigin: '0 0'}}>
					{f < part.gap ? <DayCard day={part.day} title={part.title} /> : null}
					<Sequence from={part.gap} durationInFrames={part.duration - part.gap}>
						<Diary {...part.props} />
					</Sequence>
				</div>
			</div>
			{/* right: the whole season */}
			<div style={{position: 'absolute', left: BOX_X + BOX + 70, width: FW - BOX_X - BOX - 130, top: (FH - rowH * p.days) / 2}}>
				{Array.from({length: p.days}, (_, i) => {
					const n = i + 1;
					const known = p.parts.find((x) => x.day === n);
					const now = n === part.day;
					return (
						<div key={n} style={{height: rowH, display: 'flex', alignItems: 'center', gap: 18, fontFamily: elite, fontSize: Math.min(28, rowH * 0.55), color: now ? C.red : PAPER, opacity: now ? 1 : n < part.day ? 0.55 : 0.22, whiteSpace: 'nowrap', overflow: 'hidden'}}>
							<div style={{width: 92, fontFamily: anton, fontSize: Math.min(30, rowH * 0.6), letterSpacing: 2}}>{`DAY ${n}`}</div>
							<div style={{overflow: 'hidden', textOverflow: 'ellipsis'}}>{known ? known.title.toUpperCase() : ''}</div>
						</div>
					);
				})}
			</div>
		</AbsoluteFill>
	);
};

const Outro: React.FC<{p: FilmProps}> = ({p}) => {
	const f = useCurrentFrame();
	const show = (at: number) => clamp((f - at) / 12);
	const next = p.outro.next;
	return (
		<AbsoluteFill style={{background: `rgba(0,0,0,${0.5 * show(0)})`, justifyContent: 'center', alignItems: 'center', textAlign: 'center'}}>
			<div style={{fontFamily: elite, fontSize: 120, color: PAPER}}>{typed('THE END', f, 0.35)}</div>
			{next ? (
				<>
					<div style={{fontFamily: anton, fontSize: 50, letterSpacing: 6, color: C.red, marginTop: 70, opacity: show(60)}}>A NEW STORY HAS BEGUN</div>
					<div style={{fontFamily: anton, fontSize: 110, color: '#fff', marginTop: 10, opacity: show(70)}}>{next.name.toUpperCase()}</div>
					{next.tagline ? <div style={{fontFamily: elite, fontSize: 44, color: PAPER, marginTop: 10, opacity: 0.85 * show(80)}}>{next.tagline.toUpperCase()}</div> : null}
				</>
			) : null}
			<div style={{fontFamily: anton, fontSize: 64, color: C.red, marginTop: 60, opacity: show(next ? 110 : 60)}}>SUBSCRIBE FOR THE NEXT ONE</div>
		</AbsoluteFill>
	);
};

export const Film: React.FC<FilmProps> = (p) => (
	<AbsoluteFill style={{background: '#050509'}}>
		<Backdrop grade={p.grade} />
		<Sequence durationInFrames={p.intro.duration}>
			<Intro p={p} />
		</Sequence>
		{p.parts.map((part) => (
			<Sequence key={part.day} from={part.from} durationInFrames={part.duration}>
				<Part p={p} part={part} />
			</Sequence>
		))}
		<Sequence from={p.outro.from} durationInFrames={p.outro.duration}>
			<Outro p={p} />
		</Sequence>
		{p.audio ? <Audio src={staticFile(p.audio)} /> : null}
	</AbsoluteFill>
);

// The thumbnail (1280x720): a frame of Day 1 on the right, the film's title on the left.
export const FilmThumb: React.FC<FilmProps> = (p) => {
	return (
		<AbsoluteFill style={{background: `radial-gradient(ellipse at 70% 50%, ${p.grade ?? '#3b6fb6'}55 0%, #0a0b12 60%, #050509 100%)`}}>
			<Poster p={p} height={720} right={60} />
			<div style={{position: 'absolute', left: 60, top: 0, bottom: 0, width: 720, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'flex-start'}}>
				<div style={{display: 'inline-block', fontFamily: anton, fontSize: 44, letterSpacing: 4, color: '#fff', background: C.red, padding: '6px 22px'}}>FULL STORY</div>
				<div style={{fontFamily: anton, fontSize: p.title.length > 34 ? 84 : p.title.length > 24 ? 96 : 112, lineHeight: 1.02, color: '#fff', marginTop: 28, textTransform: 'uppercase', textShadow: '0 6px 24px rgba(0,0,0,0.8)'}}>{p.title}</div>
				<div style={{fontFamily: elite, fontSize: 42, color: PAPER, marginTop: 26}}>{`ALL ${p.days} DAYS`}</div>
			</div>
		</AbsoluteFill>
	);
};
