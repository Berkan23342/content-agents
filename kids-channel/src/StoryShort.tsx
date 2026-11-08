import React from 'react';
import {AbsoluteFill, Audio, Sequence, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Look, Season, textStyle} from './common';
import {FunScene, Scenery, StoryScene, storyCam} from './Fun';

// A vertical Short cut from the day's story (written by scripts/fun.py --short): the landscape stage, zoomed to fill
// the tall frame, follows whoever is speaking. Each Short is a different moment of a different story.
type Story = Extract<FunScene, {type: 'story'}>;

export type StoryShortProps = {
	durationInFrames: number;
	audio: string;
	title: string;
	scenes: Story[];
	season?: Season;
	look?: number;
};

const K = 1920 / 1080; // the 1080-high stage fills the 1920-high frame

const TitleBand: React.FC<{title: string}> = ({title}) => {
	const f = useCurrentFrame();
	const {fps} = useVideoConfig();
	const s = spring({frame: f, fps, config: {damping: 12}});
	return (
		<div style={{position: 'absolute', top: 110, width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, transform: `scale(${s})`}}>
			<span style={{...textStyle('#2F8CFF', 44), WebkitTextStroke: '0px', filter: 'none', background: '#ffffff', padding: '8px 26px', borderRadius: 40}}>Bubbly Kids TV</span>
			<span style={{...textStyle('#FF8A1F', title.length > 22 ? 64 : 80), whiteSpace: 'normal', textAlign: 'center', maxWidth: 940}}>{title}</span>
		</div>
	);
};

export const StoryShort: React.FC<StoryShortProps> = ({scenes, audio, title, season = 'spring', look = 0}) => {
	const f = useCurrentFrame();
	const current = scenes.find((s) => f >= s.from && f < s.from + s.duration) ?? scenes[scenes.length - 1];
	const cam = storyCam(current.cam, f - current.from);
	// centre the speaker; between lines drift back to the middle of the stage
	const x = 960 + (cam.x - 960) * Math.max(0.55, cam.lean);
	const tx = Math.min(0, Math.max(1080 - 1920 * K, 540 - x * K));
	return (
		<Look.Provider value={{season, seed: look}}>
			<AbsoluteFill style={{background: '#8fd3ff', overflow: 'hidden'}}>
				<div style={{position: 'absolute', left: 0, top: 0, width: 1920, height: 1080, transform: `translate(${tx}px, 0px) scale(${K})`, transformOrigin: '0 0'}}>
					<Scenery bg={current.bg} tint={null} />
					{scenes.map((s, i) => (
						<Sequence key={i} from={s.from} durationInFrames={s.duration}>
							<StoryScene scene={s} />
						</Sequence>
					))}
				</div>
				<TitleBand title={title} />
				{audio ? <Audio src={staticFile(audio)} /> : null}
			</AbsoluteFill>
		</Look.Provider>
	);
};
