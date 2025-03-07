const mongoose = require('mongoose');

// MongoDB connection function
const connectDB = async () => {
  try {
    // The connection string uses environment variables that will be set in docker-compose
    const connectionString = process.env.MONGODB_URI || 'mongodb://mongodb:27017/billbuster';
    
    await mongoose.connect(connectionString, {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    
    console.log('MongoDB connected successfully');
    
    // Initialize schema and indexes
    await initializeSchema();
    
  } catch (error) {
    console.error('MongoDB connection error:', error.message);
    // Exit process with failure
    process.exit(1);
  }
};

// Function to initialize database schema and indexes
const initializeSchema = async () => {
  try {
    // Import Bill model
    const Bill = require('./models/Bill');
    
    // Create indexes for common search fields if they don't exist
    await Bill.collection.createIndex({ billId: 1 });
    await Bill.collection.createIndex({ state: 1 });
    await Bill.collection.createIndex({ isFederal: 1 });
    await Bill.collection.createIndex({ date: 1 });
    await Bill.collection.createIndex({ tags: 1 });
    
    console.log('MongoDB schema and indexes initialized');
  } catch (error) {
    console.error(`Error initializing schema: ${error.message}`);
  }
};

module.exports = { connectDB };