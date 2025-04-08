import { sequelize } from '../config/database';
const { Product } = require('../entities/Product')

async function syncDatabase() {
	try {
		await sequelize.sync({ alter: true }); // Creates tables if they don't exist (or alters them)
		console.log('Database synchronized successfully.');
	} catch (error) {
		console.error('Error synchronizing database:', error);
	}
}

syncDatabase(); // Run this function one time to create database

