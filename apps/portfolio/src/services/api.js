// A mock API service to simulate fetching data
export const fetchBlogPosts = async () => {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve([
        { id: 1, title: 'My First Blog Post', content: 'This is the content of my first blog post.' },
        { id: 2, title: 'Building a Monorepo', content: 'Here’s how I structured my new portfolio using pnpm.' },
        { id: 3, title: 'The Power of Vite', content: 'Why I chose Vite over other build tools for my React project.' },
        { id: 4, title: 'A Quick Guide to GraphQL', content: 'How to use GraphQL to fetch data efficiently.' },
        { id: 5, title: 'What is a CRM?', content: 'Understanding Customer Relationship Management systems.' }
      ]);
    }, 1500); // Simulate a network delay of 1.5 seconds
  });
};
