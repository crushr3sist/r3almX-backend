# wholistic Todo

- [x] setup an endpoint for rooms that user is in
- [x] integrate couplement in message and connection-service

  - [x] if there's activity in a room, all users must be notified
  - [ ] if users are offline, their notif are cached with room name and number

- [ ] notifs

  - [x] setup cache
  - [x] increment notifs if client doesn't return acknowledgement
  - [x] decrement through endpoint

- [ ] Notification Service: Develop a service to handle notifications for various events such as new messages, friend requests, room invitations, and mentions. This service can deliver notifications in real-time via websockets or push notifications.

- [ ] User Profile Service: Implement a service for managing user profiles, including features such as updating profile information, managing profile pictures, and viewing other users' profiles.

- [ ] Search Service: Create a search service to enable users to search for rooms, channels, users, or messages within your application. Implement search functionality using full-text search capabilities provided by your database or integrate with a dedicated search engine like Elasticsearch.

- [ ] Media Service: Add support for users to upload and share media files such as images, videos, and documents within chat rooms and social posts. Develop a service to manage media storage, retrieval, and sharing.

- [ ] Analytics Service: Integrate an analytics service to track user engagement, activity, and behavior within your application. Collect data on metrics such as active users, message volume, popular rooms, and user interactions to gain insights into user behavior and preferences.

- [ ] Content Moderation Service: Implement a service for content moderation to ensure that user-generated content complies with community guidelines and legal requirements. Develop features such as profanity filters, spam detection, and moderation tools for managing reported content.

- [ ] Integration Service: Create an integration service to facilitate integrations with external services and APIs. This service can handle tasks such as fetching data from external sources, sending notifications to third-party systems, and synchronizing data between your application and external platforms.

- [ ] Backup Service: Set up a backup service to regularly backup your database and critical data to prevent data loss in case of hardware failures, accidents, or other unforeseen events. Develop a backup strategy and schedule to ensure data integrity and availability.

- [ ] Monitoring and Logging Service: Implement a monitoring and logging service to track the health and performance of your application in real-time. Monitor metrics such as server uptime, response times, error rates, and resource usage to identify and address issues proactively.

- [ ] Documentation and API Gateway: Create comprehensive documentation for your backend services and APIs. Implement an API gateway to provide a unified entry point for accessing your backend services and manage authentication, rate limiting, and other cross-cutting concerns.

# social media todo

- [ ] Define Post Model: Create a database model for posts. This model should include fields such as post content, author ID, creation timestamp, likes count, comments count, and any other relevant metadata.

- [ ] Implement CRUD Operations: Develop APIs for creating, reading, updating, and deleting posts. These APIs should allow users to create new posts, view posts from their own feed or specific users, edit their own posts, and delete posts they've created.

- [ ] User Interaction Features: Implement features for users to interact with posts, such as liking, commenting, and sharing. Each interaction should be stored in the database and reflected in the post's metadata.

- [ ] Feed Generation: Create algorithms to generate user feeds based on their interests, followed users, and trending topics. Users should see a personalized feed of posts from users they follow, along with recommendations for new users to follow and trending topics to explore.

- [ ] Hashtags and Mentions: Implement support for hashtags and user mentions in posts. Users should be able to include hashtags to categorize their posts and mention other users to notify them and link to their profiles.

- [ ] Real-time Updates: Use websockets or push notifications to deliver real-time updates to users' feeds, notifications, and interactions. Users should be notified instantly when new posts are published, liked, or commented on.

- [ ] Explore and Discover: Create features for users to explore and discover new content and users within the platform. This could include trending hashtags, popular posts, recommended users to follow, and personalized recommendations based on user interests and behavior.

- [ ] Content Moderation: Implement moderation tools to ensure that user-generated content complies with community guidelines and legal requirements. This may include features such as spam detection, profanity filters, and reporting mechanisms for inappropriate content.

- [ ] Analytics and Insights: Integrate analytics tools to track user engagement, post reach, and audience demographics. Provide users with insights into their post performance and audience engagement to help them optimize their content strategy.

- [ ] Integration with Rooms and Channels: Ensure seamless integration between the social media platform and your existing rooms and channels features. Users should be able to share posts in rooms, comment on room discussions, and interact with other users across different parts of the application.

- [ ] User Profiles and Settings: Develop features for users to manage their profiles, settings, and privacy preferences. Users should be able to customize their profile information, adjust privacy settings, and control who can see their posts and interact with them.

# Feed Generation

- [ ] Personalized Feeds: Use metadata about users, posts, and interactions to generate personalized feeds for each user. Consider factors such as the user's interests, followed users, trending topics, and past interactions to curate a feed that's relevant and engaging.

- [ ] Algorithmic Ranking: Develop algorithms to rank posts in the feed based on factors such as recency, relevance, popularity, and user engagement. Experiment with different ranking algorithms and fine-tune them based on user feedback and performance metrics.

- [ ] Followers' Feeds: Generate separate feeds for each user's followers, showing posts from users they follow in chronological or algorithmically-ranked order. This allows users to stay updated on the latest content from their friends and favorite accounts.

- [ ] Trending Topics: Identify trending hashtags, topics, and keywords within the platform based on post metadata and user interactions. Highlight trending content in users' feeds and provide tools for users to explore and participate in trending discussions.

- [ ] Recommendation Engine: Use machine learning algorithms to provide personalized recommendations for users to discover new content, users, and topics. Analyze user behavior, preferences, and past interactions to generate recommendations that are tailored to each user's interests.

- [ ] Real-time Updates: Ensure that feeds are updated in real-time to reflect changes such as new posts, likes, comments, and shares. Use websockets or push notifications to deliver updates to users' feeds instantly, keeping them engaged and informed.

# Meta Data

- [ ] Post Metadata: Include metadata fields in your post model to store additional information about each post. This may include attributes such as post ID, author ID, creation timestamp, likes count, comments count, shares count, and any other relevant data.

- [ ] User Metadata: Store metadata about users to personalize their experience and improve feed generation. This may include attributes such as user ID, username, profile picture, bio, followers count, following count, and any other user-specific data.

- [ ] Post Interaction Metadata: Track interactions such as likes, comments, and shares on each post. Store this data separately and update the corresponding post metadata to reflect changes in engagement.

- [ ] Hashtag and Mention Metadata: Index hashtags and mentions used in posts to facilitate search and discovery. Store metadata about each hashtag and mention, including the posts they're associated with, to generate related content and recommendations.

- [ ] Feed Preferences: Allow users to customize their feed preferences based on their interests, followed users, and other criteria. Store user preferences as metadata and use them to generate personalized feeds tailored to each user's preferences.

# whats already implemented

- [x] auth service

  - [x] login
  - [x] register
  - [x] jwt tokens

- [x] room service :p

  - [x] create
  - [x] read
  - [x] join
  - [x] delete
  - [x] edit name

- [x] invite service
  - [x] handle joining
