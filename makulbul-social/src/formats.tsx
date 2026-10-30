import React from 'react';
import {AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {BODY, Backdrop, C, DISPLAY, Device, Headline, Logo, MONO, Pill, Rise, clamp, useIn} from './brand';

// ---------------------------------------------------------------- specs (written by the daily agent, see AGENT.md)
type Product = {name: string; short: string};
export type Spec = {audio?: string} & (
	| {
			format: 'compare';
			hook: string;
			category: 'telefon' | 'laptop';
			a: Product;
			b: Product;
			rows: {label: string; a: string; b: string; win: 'a' | 'b' | 'tie'}[];
			verdict: string;
	  }
	| {format: 'myth'; claim: string; truth: string; points: string[]}
	| {format: 'versus'; question: string; options: {title: string; lines: string[]}[]; ask: string}
	| {format: 'tips'; title: string; items: {big: string; small: string}[]}
	| {format: 'fact'; kicker: string; big: string; small: string}
);

const CTA = 66; // end card frames

/** Length of the reel in frames; keep in sync with the timelines below. */
export const reelFrames = (s: Spec) => {
	switch (s.format) {
		case 'compare':
			return 66 + 42 * s.rows.length + 80 + CTA;
		case 'myth':
			return 120 + 38 * s.points.length + 45 + CTA;
		case 'versus':
			return 190 + CTA;
		case 'tips':
			return 55 + 66 * s.items.length + CTA;
		case 'fact':
			return 165 + CTA;
	}
};

// ---------------------------------------------------------------- shared pieces
const Header: React.FC = () => (
	<div style={{position: 'absolute', top: 110, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
		<Logo size={46} />
	</div>
);

const EndCard: React.FC<{from: number}> = ({from}) => {
	const frame = useCurrentFrame();
	const s = useIn(from, 12);
	if (frame < from) return null;
	return (
		<AbsoluteFill style={{background: C.bg, opacity: clamp((frame - from) / 8), justifyContent: 'center', alignItems: 'center', gap: 40}}>
			<div style={{transform: `scale(${0.8 + s * 0.2})`}}>
				<Logo size={90} />
			</div>
			<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 86, color: C.deal, letterSpacing: '-0.02em'}}>makulbul.com</div>
			<div style={{fontFamily: BODY, fontWeight: 500, fontSize: 44, color: C.muted, textAlign: 'center', maxWidth: 820}}>
				Bütçene ve ihtiyacına uygun cihazı saniyeler içinde bul.
			</div>
		</AbsoluteFill>
	);
};

const Card: React.FC<{children: React.ReactNode; style?: React.CSSProperties; glow?: string}> = ({children, style, glow}) => (
	<div
		style={{
			background: C.surface,
			border: `2px solid ${glow ?? C.border}`,
			borderRadius: 36,
			boxShadow: glow ? `0 0 60px ${glow}44` : '0 20px 60px rgba(0,0,0,0.45)',
			...style,
		}}
	>
		{children}
	</div>
);

// ---------------------------------------------------------------- compare: two real models, specs only (no prices)
const Compare: React.FC<{s: Extract<Spec, {format: 'compare'}>; still?: boolean}> = ({s, still}) => {
	const frame = useCurrentFrame();
	const inA = useIn(still ? -99 : 6);
	const inB = useIn(still ? -99 : 14);
	const vs = useIn(still ? -99 : 24, 8);
	const rowsAt = 66;
	const verdictAt = rowsAt + 42 * s.rows.length;
	const devW = s.category === 'laptop' ? (still ? 250 : 320) : still ? 130 : 170;
	const score = (side: 'a' | 'b') => s.rows.filter((r, i) => r.win === side && (still || frame >= rowsAt + i * 42 + 14)).length;
	return (
		<AbsoluteFill>
			{still ? null : (
				<div style={{position: 'absolute', top: 210, left: 60, right: 60}}>
					<Headline text={s.hook} at={0} size={74} highlight={[]} />
				</div>
			)}
			<div style={{position: 'absolute', top: still ? 70 : 420, left: 0, right: 0, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 50}}>
				{(['a', 'b'] as const).map((side, k) => {
					const p = s[side];
					const sIn = k === 0 ? inA : inB;
					return (
						<React.Fragment key={side}>
							{k === 1 ? (
								<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 80, color: C.deal, transform: `scale(${vs})`}}>VS</div>
							) : null}
							<div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, opacity: clamp(sIn * 1.4), transform: `translateX(${(1 - sIn) * (k ? 200 : -200)}px)`}}>
								<Device kind={s.category} label={p.short} accent={k ? C.deal : C.signal} width={devW} />
								<div style={{fontFamily: BODY, fontWeight: 700, fontSize: 36, color: C.text, maxWidth: 400, textAlign: 'center'}}>{p.name}</div>
								<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 40, color: k ? C.deal : C.signal}}>{score(side)} puan</div>
							</div>
						</React.Fragment>
					);
				})}
			</div>
			<div style={{position: 'absolute', top: still ? 480 : s.category === 'laptop' ? 840 : 890, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: still ? 16 : 12}}>
				{s.rows.map((r, i) => {
					const at = rowsAt + i * 42;
					if (!still && frame < at) return null;
					const won = still || frame >= at + 14;
					const cell = (side: 'a' | 'b') => {
						const hot = won && (r.win === side || r.win === 'tie');
						return (
							<div style={{flex: 1, textAlign: side === 'a' ? 'left' : 'right', fontFamily: MONO, fontWeight: 600, fontSize: 40, color: hot ? C.deal : C.muted}}>
								{side === 'a' && hot && r.win !== 'tie' ? '✓ ' : ''}
								{r[side]}
								{side === 'b' && hot && r.win !== 'tie' ? ' ✓' : ''}
							</div>
						);
					};
					return (
						<Rise key={i} at={still ? -99 : at} dist={40}>
							<Card style={{display: 'flex', alignItems: 'center', padding: still ? '22px 34px' : '18px 34px', gap: 20}}>
								{cell('a')}
								<div style={{fontFamily: BODY, fontWeight: 700, fontSize: 34, color: C.text, textAlign: 'center', minWidth: 230}}>{r.label}</div>
								{cell('b')}
							</Card>
						</Rise>
					);
				})}
			</div>
			{still || frame >= verdictAt ? (
				<Rise at={still ? -99 : verdictAt} style={{position: 'absolute', left: 70, right: 70, bottom: still ? 120 : 280}}>
					<Card glow={C.deal} style={{padding: '30px 40px', textAlign: 'center'}}>
						<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 48, color: C.text, lineHeight: 1.2}}>{s.verdict}</div>
					</Card>
				</Rise>
			) : null}
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- myth: a common belief, struck through, then the truth
const Myth: React.FC<{s: Extract<Spec, {format: 'myth'}>; still?: boolean}> = ({s, still}) => {
	const frame = useCurrentFrame();
	const strike = still ? 1 : clamp((frame - 48) / 12);
	const stamp = useIn(still ? -99 : 58, 8);
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: still ? 120 : 330, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
				<Pill color="#3a1414" ink={C.danger}>Yaygın yanlış</Pill>
			</div>
			<div style={{position: 'absolute', top: still ? 230 : 460, left: 70, right: 70}}>
				<div style={{position: 'relative'}}>
					<Headline text={s.claim} at={still ? -99 : 4} size={still ? 96 : 120} />
					<div style={{position: 'absolute', left: '4%', top: '48%', height: 14, width: `${92 * strike}%`, background: C.danger, borderRadius: 8, transform: 'rotate(-4deg)'}} />
				</div>
				<div style={{display: 'flex', justifyContent: 'center', marginTop: 30, transform: `scale(${stamp}) rotate(-6deg)`}}>
					<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 52, color: C.danger, border: `5px solid ${C.danger}`, borderRadius: 16, padding: '6px 26px'}}>YANLIŞ</div>
				</div>
			</div>
			<Rise at={still ? -99 : 82} style={{position: 'absolute', top: still ? 620 : 960, left: 70, right: 70}}>
				<Card glow={C.deal} style={{padding: '34px 40px'}}>
					<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 34, color: C.deal, marginBottom: 12}}>GERÇEK</div>
					<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 56, color: C.text, lineHeight: 1.15}}>{s.truth}</div>
				</Card>
			</Rise>
			<div style={{position: 'absolute', top: still ? 930 : 1310, left: 90, right: 90, display: 'flex', flexDirection: 'column', gap: 18}}>
				{s.points.map((p, i) => (
					<Rise key={i} at={still ? -99 : 120 + i * 38} dist={30}>
						<div style={{fontFamily: BODY, fontWeight: 700, fontSize: 42, color: C.text, display: 'flex', gap: 18}}>
							<span style={{color: C.signal}}>→</span>
							{p}
						</div>
					</Rise>
				))}
			</div>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- versus: two options, the viewer picks (comment bait)
const Versus: React.FC<{s: Extract<Spec, {format: 'versus'}>; still?: boolean}> = ({s, still}) => {
	const frame = useCurrentFrame();
	const pulse = 1 + Math.sin(frame / 6) * 0.04;
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: still ? 130 : 330, left: 60, right: 60}}>
				<Headline text={s.question} at={still ? -99 : 2} size={still ? 100 : 118} highlight={s.options.map((o) => o.title.split(' ')[0])} />
			</div>
			<div style={{position: 'absolute', top: still ? 480 : 760, left: 60, right: 60, display: 'flex', gap: 34}}>
				{s.options.map((o, k) => (
					<Rise key={k} at={still ? -99 : 40 + k * 22} dist={80} style={{flex: 1}}>
						<Card glow={k ? C.deal : C.signal} style={{padding: '44px 34px', minHeight: still ? 520 : 560}}>
							<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 78, color: k ? C.deal : C.signal, textAlign: 'center', marginBottom: 30}}>{o.title}</div>
							{o.lines.map((l, i) => (
								<div key={i} style={{fontFamily: BODY, fontWeight: 700, fontSize: 40, color: C.text, textAlign: 'center', marginBottom: 18}}>
									{l}
								</div>
							))}
						</Card>
					</Rise>
				))}
			</div>
			<Rise at={still ? -99 : 120} style={{position: 'absolute', bottom: still ? 110 : 380, left: 0, right: 0, textAlign: 'center'}}>
				<div style={{display: 'inline-block', transform: `scale(${still ? 1 : pulse})`, fontFamily: DISPLAY, fontWeight: 700, fontSize: 64, color: C.text}}>{s.ask}</div>
			</Rise>
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- tips: one tip per screen, big and short
const Tips: React.FC<{s: Extract<Spec, {format: 'tips'}>; still?: boolean}> = ({s, still}) => {
	const frame = useCurrentFrame();
	if (still) {
		return (
			<AbsoluteFill>
				<div style={{position: 'absolute', top: 130, left: 70, right: 70}}>
					<Headline text={s.title} at={-99} size={84} />
				</div>
				<div style={{position: 'absolute', top: 400, left: 70, right: 70, display: 'flex', flexDirection: 'column', gap: 30}}>
					{s.items.map((it, i) => (
						<Card key={i} style={{padding: '26px 34px', display: 'flex', gap: 28, alignItems: 'center'}}>
							<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 72, color: C.deal, minWidth: 70}}>{i + 1}</div>
							<div>
								<div style={{fontFamily: DISPLAY, fontWeight: 700, fontSize: 58, color: C.text}}>{it.big}</div>
								<div style={{fontFamily: BODY, fontWeight: 500, fontSize: 38, color: C.muted, marginTop: 6}}>{it.small}</div>
							</div>
						</Card>
					))}
				</div>
			</AbsoluteFill>
		);
	}
	const idx = Math.floor((frame - 55) / 66);
	return (
		<AbsoluteFill>
			<div style={{position: 'absolute', top: 300, left: 60, right: 60, opacity: idx < 0 ? 1 : 0.35, transform: `scale(${idx < 0 ? 1 : 0.62}) translateY(${idx < 0 ? 0 : -180}px)`, transition: 'none'}}>
				<Headline text={s.title} at={2} size={110} />
			</div>
			{s.items.map((it, i) => {
				const at = 55 + i * 66;
				if (frame < at || frame >= at + 66) return null;
				return (
					<Sequence key={i} from={at} durationInFrames={66}>
						<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 70px'}}>
							<Rise at={0}>
								<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 210, color: C.deal, textAlign: 'center', lineHeight: 1}}>
									{i + 1}/{s.items.length}
								</div>
							</Rise>
							<div style={{marginTop: 40}}>
								<Headline text={it.big} at={4} size={112} />
							</div>
							<Rise at={14} style={{marginTop: 40}}>
								<div style={{fontFamily: BODY, fontWeight: 700, fontSize: 50, color: C.muted, textAlign: 'center', lineHeight: 1.25}}>{it.small}</div>
							</Rise>
						</AbsoluteFill>
					</Sequence>
				);
			})}
		</AbsoluteFill>
	);
};

// ---------------------------------------------------------------- fact: one surprising fact
const Fact: React.FC<{s: Extract<Spec, {format: 'fact'}>; still?: boolean}> = ({s, still}) => (
	<AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', padding: '0 70px', gap: 50}}>
		<Rise at={still ? -99 : 0}>
			<Pill>{s.kicker}</Pill>
		</Rise>
		<Headline text={s.big} at={still ? -99 : 12} size={still ? 100 : 124} highlight={[]} />
		<Rise at={still ? -99 : 60}>
			<div style={{fontFamily: BODY, fontWeight: 700, fontSize: still ? 44 : 52, color: C.muted, textAlign: 'center', lineHeight: 1.3}}>{s.small}</div>
		</Rise>
	</AbsoluteFill>
);

const Body: React.FC<{spec: Spec; still?: boolean}> = ({spec, still}) => {
	switch (spec.format) {
		case 'compare':
			return <Compare s={spec} still={still} />;
		case 'myth':
			return <Myth s={spec} still={still} />;
		case 'versus':
			return <Versus s={spec} still={still} />;
		case 'tips':
			return <Tips s={spec} still={still} />;
		case 'fact':
			return <Fact s={spec} still={still} />;
	}
};

// ---------------------------------------------------------------- compositions
export const Reel: React.FC<Spec> = (spec) => {
	const total = reelFrames(spec);
	const frame = useCurrentFrame();
	const fadeIn = interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'});
	return (
		<AbsoluteFill lang="tr" style={{opacity: fadeIn}}>
			<Backdrop accent={spec.format === 'myth' ? C.danger : C.signal} />
			<Header />
			<Body spec={spec} />
			<EndCard from={total - CTA} />
			{spec.audio ? <Audio src={staticFile(spec.audio)} /> : null}
		</AbsoluteFill>
	);
};

export const Post: React.FC<Spec> = (spec) => (
	<AbsoluteFill lang="tr">
		<Backdrop accent={spec.format === 'myth' ? C.danger : C.signal} />
		<Body spec={spec} still />
		<div style={{position: 'absolute', bottom: 46, left: 70, right: 70, display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
			<Logo size={40} />
			<div style={{fontFamily: MONO, fontWeight: 600, fontSize: 34, color: C.deal}}>makulbul.com</div>
		</div>
	</AbsoluteFill>
);
