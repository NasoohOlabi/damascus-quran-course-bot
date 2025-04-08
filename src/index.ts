require('dotenv').config();
const { Telegraf } = require('telegraf');
import { sequelize } from './config/database';
import { Product } from "./entities/Product";

sequelize.sync()

const bot = new Telegraf(process.env.BOT_TOKEN);

// --- Helper function to format product information ---
function formatProduct(product) {
	return `ID: ${product.id}\nName: ${product.name}\nDescription: ${product.description || 'N/A'}\nPrice: $${product.price}\nCreated At: ${product.createdAt}\nCreated By: ${product.createdBy || 'N/A'}\nModified At: ${product.modifiedAt || 'N/A'}\nModified By: ${product.modifiedBy || 'N/A'}`;
}

// --- Create Product ---
bot.command('create', async (ctx) => {
	try {
		// Example: /create ProductName Description 19.99
		const parts = ctx.message.text.split(' ');
		if (parts.length < 4) {
			return ctx.reply('Usage: /create <name> <description> <price>');
		}
		const name = parts[1];
		const description = parts[2];
		const price = parseFloat(parts[3]);

		if (isNaN(price)) {
			return ctx.reply('Invalid price. Please enter a number.');
		}

		const product = await Product.create({
			name,
			description,
			price,
			createdBy: ctx.from.username || ctx.from.first_name,
		});

		ctx.reply(`Product created successfully:\n${formatProduct(product)}`);
	} catch (error) {
		console.error('Error creating product:', error);
		ctx.reply(`Error creating product: ${error.message}`);
	}
});

// --- Read Product ---
bot.command('read', async (ctx) => {
	try {
		// Example: /read 1 (where 1 is the product ID)
		const parts = ctx.message.text.split(' ');
		if (parts.length !== 2) {
			return ctx.reply('Usage: /read <product_id>');
		}
		const productId = parseInt(parts[1], 10);

		if (isNaN(productId)) {
			return ctx.reply('Invalid product ID. Please enter a number.');
		}

		const product = await Product.findByPk(productId);

		if (!product) {
			return ctx.reply('Product not found.');
		}

		ctx.reply(`Product details:\n${formatProduct(product)}`);
	} catch (error) {
		console.error('Error reading product:', error);
		ctx.reply(`Error reading product: ${error.message}`);
	}
});

// --- Update Product ---
bot.command('update', async (ctx) => {
	try {
		// Example: /update 1 ProductName NewDescription 29.99
		const parts = ctx.message.text.split(' ');
		if (parts.length < 5) {
			return ctx.reply('Usage: /update <id> <name> <description> <price>');
		}

		const productId = parseInt(parts[1], 10);
		const name = parts[2];
		const description = parts[3];
		const price = parseFloat(parts[4]);

		if (isNaN(productId) || isNaN(price)) {
			return ctx.reply('Invalid ID or price. Please enter numbers.');
		}

		const product = await Product.findByPk(productId);

		if (!product) {
			return ctx.reply('Product not found.');
		}

		product.name = name;
		product.description = description;
		product.price = price;
		product.modifiedBy = ctx.from.username || ctx.from.first_name;

		await product.save();

		ctx.reply(`Product updated successfully:\n${formatProduct(product)}`);
	} catch (error) {
		console.error('Error updating product:', error);
		ctx.reply(`Error updating product: ${error.message}`);
	}
});

// --- Delete Product ---
bot.command('delete', async (ctx) => {
	try {
		// Example: /delete 1
		const parts = ctx.message.text.split(' ');
		if (parts.length !== 2) {
			return ctx.reply('Usage: /delete <product_id>');
		}

		const productId = parseInt(parts[1], 10);

		if (isNaN(productId)) {
			return ctx.reply('Invalid product ID. Please enter a number.');
		}

		const product = await Product.findByPk(productId);

		if (!product) {
			return ctx.reply('Product not found.');
		}

		await product.destroy();

		ctx.reply('Product deleted successfully.');
	} catch (error) {
		console.error('Error deleting product:', error);
		ctx.reply(`Error deleting product: ${error.message}`);
	}
});

// --- Start the bot ---
bot.start((ctx) => ctx.reply('Welcome to the CRUD bot! Use /create, /read, /update, /delete.'));

bot.launch();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

