import { DataTypes } from 'sequelize';
import { BaseEntity } from './BaseEntity';

export class Product extends BaseEntity {
	static initModel() {
		return super.initModel(
			{
				name: {
					type: DataTypes.STRING,
					allowNull: false,
				},
				price: {
					type: DataTypes.DECIMAL(10, 2),
					allowNull: false,
				},
			},
			{
				modelName: 'Product',
				tableName: 'products',
			}
		);
	}
}

// Initialize the model
Product.initModel();
