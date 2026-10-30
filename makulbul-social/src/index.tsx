import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Post, Reel, Spec, reelFrames} from './formats';

// Real props come from content/<date>/spec.json via `--props`; this is only a Studio placeholder.
const sample: Spec = {
	format: 'versus',
	question: '128 GB mı, 256 GB mı?',
	options: [
		{title: '128 GB', lines: ['Mesajlaşma', 'Sosyal medya', 'Az fotoğraf']},
		{title: '256 GB', lines: ['Bol video', 'Oyun', 'Yıllarca rahat']},
	],
	ask: 'Sen hangisisin? 👇',
};

const Root: React.FC = () => (
	<>
		<Composition
			id="Reel"
			component={Reel}
			defaultProps={sample}
			calculateMetadata={({props}) => ({durationInFrames: reelFrames(props)})}
			durationInFrames={300}
			fps={30}
			width={1080}
			height={1920}
		/>
		<Composition id="Post" component={Post} defaultProps={sample} durationInFrames={1} fps={30} width={1080} height={1350} />
	</>
);

registerRoot(Root);
