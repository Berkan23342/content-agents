import React from 'react';
import {AbsoluteFill, Composition, registerRoot} from 'remotion';
import {Defs, Walker} from './art';
import {Diary, DiaryProps} from './Diary';

// Real props come from build/<id>/props.json via `--props`; this is only a Studio placeholder.
const placeholder: DiaryProps = {
	durationInFrames: 90,
	audio: '',
	day: 1,
	episode: 1,
	title: 'The Sirens',
	beats: [
		{from: 0, duration: 90, scene: 'building', p: {zombies: 3}, cam: 'push', tone: 'night', rain: false, fog: false, flashlight: false, alarm: false, cutIn: false, cutOut: false, hits: []},
	],
	chunks: [],
	endAt: 999,
};

/** Channel avatar: a lone walker under a red moon. */
const Avatar: React.FC = () => (
	<AbsoluteFill style={{background: 'radial-gradient(circle at 50% 40%, #3a0d12 0%, #07080d 75%)'}}>
		<svg width={800} height={800} viewBox="0 0 800 800">
			<Defs />
			<circle cx={400} cy={330} r={190} fill="#b3201d" />
			<circle cx={400} cy={330} r={260} fill="#b3201d" opacity={0.15} />
			<Walker x={360} y={720} h={560} frame={8} seed={0} eyes />
			<rect x={0} y={700} width={800} height={100} fill="#07080d" />
		</svg>
	</AbsoluteFill>
);

const Root: React.FC = () => (
	<>
		<Composition
			id="Diary"
			component={Diary}
			defaultProps={placeholder}
			calculateMetadata={({props}) => ({durationInFrames: props.durationInFrames})}
			durationInFrames={90}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition id="Avatar" component={Avatar} durationInFrames={1} fps={30} width={800} height={800} />
	</>
);

registerRoot(Root);
